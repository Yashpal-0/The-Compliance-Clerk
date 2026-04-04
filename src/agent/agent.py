"""
Agent loop using OpenAI function calling.

Key differences from Anthropic:
- client = openai.OpenAI()
- Tool calls live in response.choices[0].message.tool_calls
- Each tool call has .function.name and .function.arguments (JSON string)
- Tool results go back as role="tool" messages with tool_call_id
- tool_choice="required" forces a tool call (equivalent to Anthropic's "any")
- tool_choice="auto" lets the model decide
"""

import json
import openai
from src.tools.tools import TOOLS, EXTRACTION_TOOLS
from src.audit.audit import log_extraction

client = openai.OPENAI()

SYSTEM_PROMPT = """You are a document extraction specialist for Indian government 
and legal documents, particularly from Gujarat.

Documents may be in English, Gujarati, or a mix of both. 
You can read and extract from both languages.

Your workflow:
1. ALWAYS call classify_document first to identify what's in the PDF.
2. Then call the appropriate extraction tool(s) for each document type found.
   - If a PDF contains both e-Challans AND a Lease Deed, call extraction tools for EACH.
   - For multiple e-Challans (e.g., Registration Fee + Stamp Duty), call extract_echallan_fields ONCE PER CHALLAN.
3. If a field is genuinely absent, omit it — never fabricate values.
4. If the document is unreadable, call flag_extraction_failure.

Key patterns to recognize:
- NA Orders: Start with "iORA/" order numbers, issued by Prant Kacheri
- e-Challans: Issued by Inspector General of Registration, have Transaction No.
- Lease Deeds: Have DNR number box (top right), "LEASE DEED / લીઝનોકરાર" heading
- Gujarati: ચો.મી. = sq.mt., તા. = date, જિ. = district, તા. = taluka/date (context-dependent)
"""

def run_agent(pdf_path: str, doc_text: str, hint_types: list) -> tuple[list,list]:
    """
    Agent loop that extracts ALL records from a PDF.
    A single PDF can produce multiple records of different types.
    
    Returns: (list_of_records, list_of_doc_types_found)
    """

    user_message = f"""Extract ALL documents from this PDF file. 

File: {pdf_path}
Pre-detected hints: {hint_types}

IMPORTANT: This PDF may contain MULTIPLE documents. For example:
- Multiple e-Challans (one for Registration Fee, one for Stamp Duty)
- Plus a Lease Deed
- Plus other supporting docs

Call extract_echallan_fields ONCE PER CHALLAN found.
Call extract_lease_deed_fields if a lease deed is present.
Call extract_na_order_fields if an NA order is present.

Document text (with page breaks marked):
---
{doc_text}
---"""
    messages = [{"role": "system", "content": user_message},
    {
            "role": "user",
            "content": (
                f"Extract ALL documents from this PDF file.\n\n"
                f"File: {pdf_path}\n"
                f"Pre-detected hints: {hint_types}\n\n"
                f"IMPORTANT: This PDF may contain MULTIPLE documents. For example:\n"
                f"- Multiple e-Challans (Registration Fee + Stamp Duty)\n"
                f"- Plus a Lease Deed\n"
                f"- Plus other supporting docs\n\n"
                f"Call extract_echallan_fields ONCE PER CHALLAN found.\n\n"
                f"Document text:\n---\n{doc_text}\n---"
            )
        }
        ]
        
    extracted_records = []
    classification = []
    max_iteration = 10

    for iteration in range(max_iteration):

        tool_choice = "required" if iteration == 0 else "auto"

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOLS,
            tool_choice=tool_choice,
            temperature=0, # deterministic extraction
            max_tokens=4096
        )

        message=response.choices[0].message

        messages.append(message)

        if not message.tool_calls:
            break

        tool_result_messages = []

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            try:
                tool_input = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_input = {}

            log_extraction(
                source_file=pdf_path,
                extraction_method="openai-agent",
                doc_types=classification,
                tool_called=tool_name,
                tool_input=tool_input,
                raw_response={
                    "model": response.model,
                    "iteratioin": iteration,
                    "stop_reason":response.choices[0].finish_reason
                }
            )

            if tool_name == "classify_document":
                classification = tool_input.get("doc_types_found",[])

                expected = []

                if "echallan" in classification:
                    expected.append("call extract_echallan_fields for EACH challan")
                if "lease_deed" in classification:
                    expected.append("call extract_lease_deed_fields")
                if "na_order" in classification:
                    expected.append("call extract_na_order_fields")

                result_content = (
                    f"Classification done: {classification}. "
                    f"Now you must: {'; '.join(expected)}"
                    f"Do not stop until all types are extracted."
                )

            elif tool_name in EXTRACTION_TOOLS:
                doc_type = tool_name.replace("extract_", "").replace("_fields", "")
                record = {
                    "doc_type": doc_type,
                    "source_file": pdf_path,
                    **tool_input
                }
                extracted_records.append(record)

                same_type_count = sum(
                    1 for r in extracted_records if r["doc_type"]==doc_type

                )

                if tool_name == "extract_echallan_fields":
                    result_content = (
                        f"Challan #{same_type_count} extracted "
                        f"({tool_input.get('account_head', '')}). "
                        f"Are there more challans? If yes, call extract_echallan_fields "
                        f"again. If no more, extract remaining document types."
                    )
                else:
                    result_content = (
                        f"Extracted {doc_type} successfully (record #{same_type_count})."
                    )

            elif tool_name == "flag_extraction_failure":
                log_extraction(
                    source_file=pdf_path,
                    extraction_method="openai-agent",
                    doc_types=classifications,
                    tool_called=tool_name,
                    tool_input=tool_input,
                    raw_response={},
                    status="failure",
                    error_message=tool_input.get("reason")
                )
                result_content = f"Failure flagged: {tool_input.get('reason')}"

            else:
                result_content = "Unknown tool called."

            # OpenAI tool results use role="tool" with tool_call_id
            tool_result_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_content
            })

        messages.append(tool_result_messages)

        if _all_types_extracted(classification, extracted_records):
            break

        if response.choices[0].finish_reason == "stop":
            break

    return extracted_records, classification


def _all_type_extracted(classifications: list, records: list)-> bool:
    """Check if agent has extracted atleast one record for each classified type."""

    if not classifications or "unknown" in classifications:
        return len(records) > 0
    
    extracted_types = {r["doc_type"] for r in records}
    
    type_map = {
        "na_order": "na_order",
        "echallan": "echallan",
        "lease_deed": "lease_deed"
    }

    for cls_type in classifications:
        mapped = type_map.get(cls_type)

        if mapped and mapped not in extracted_types:
            return False

    return True 



