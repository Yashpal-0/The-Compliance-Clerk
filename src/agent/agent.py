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
import os
import openai
import time
from dotenv import load_dotenv
from src.tools.tools import TOOLS, EXTRACTION_TOOLS
from src.audit.audit import log_extraction
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()

# We can reuse the OpenAI SDK to perfectly interface with OpenRouter
client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

SYSTEM_PROMPT = """You are a document extraction specialist for Indian government 
and legal documents, particularly from Gujarat.

Documents may be in English, Gujarati, or a mix of both. 
You can read and extract from both languages.

Your workflow:
1. ALWAYS call classify_document first to identify what's in the PDF.
2. Then call the appropriate extraction tool(s) for each document type found.
   - If a PDF contains multiple NA PDFs, eChallans, or Lease Deeds, call extraction tools for EACH.
3. If a field is genuinely absent, omit it — never fabricate values.
4. If the document is unreadable, call flag_extraction_failure.

Key patterns to recognize:
- NA PDF: Start with "iORA/" order numbers, Survey Number, Land Area, Owner Name.
- eChallans (Traffic/Violation): Details like Challan Number, Vehicle Number, Offence Description. 
  NOTE: ONLY extract Traffic Violation eChallans using extract_echallan_fields. DO NOT use extract_echallan_fields for Stamp Duty or Registration Fee receipts.
- Lease Deed: Look for Lease Deeds, Registration Fees, and Stamp Duty.
- Gujarati: ચો.મી. = sq.mt., તા. = date, જિ. = district, તા. = taluka/date (context-dependent)
"""

@retry(wait=wait_exponential(multiplier=1, min=15, max=60), stop=stop_after_attempt(5), retry=retry_if_exception_type(openai.RateLimitError), reraise=True)
def run_agent(pdf_path: str, doc_text: str, hint_types: list) -> tuple[list,list]:
    """
    Agent loop that extracts ALL records from a PDF.
    A single PDF can produce multiple records of different types.
    """

    user_message = f"""Extract ALL documents from this PDF file.

File: {pdf_path}
Pre-detected hints: {hint_types}

IMPORTANT: This PDF may contain MULTIPLE documents. For example:
- Traffic eChallans, NA orders, or Lease Deeds

Call extract_echallan_fields for EACH Traffic challan found (Strictly ignore property stamp duty receipts).
Call extract_na_order_fields for each NA order present.
Call extract_lease_deed_fields for Lease Deeds.

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
                f"IMPORTANT: This PDF may contain MULTIPLE documents.\n"
                f"Call extract_echallan_fields OR extract_na_order_fields OR extract_lease_deed_fields as needed.\n\n"
                f"Document text:\n---\n{doc_text}\n---"
            )
        }
        ]
        
    extracted_records = []
    classification = []
    max_iteration = 10

    for iteration in range(max_iteration):

        tool_choice = "auto"

        response = client.chat.completions.create(
            model="qwen/qwen3.6-plus:free", # OpenRouter model requested
            messages=messages,
            tools=TOOLS,
            tool_choice=tool_choice,
            temperature=0, # deterministic extraction
        )

        # ADD THIS: Print the raw response to see what the API actually returned
        if not response or not response.choices:
            print(f"\n[DEBUG] Raw API Response: {response}")
            print(f"[DEBUG] Response type: {type(response)}")
            # Raise an exception so you can see the log and let Tenacity retry if you want
            raise ValueError(f"Malformed Response: {response}")

        message=response.choices[0].message

        messages.append(message)

        if not message.tool_calls:
            if _all_types_extracted(classification, extracted_records):
                break
            else:
                messages.append({"role": "user", "content": "You must call the appropriate extraction tools to complete the task."})
                continue

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
                },
                prompt_messages=[m.model_dump() if hasattr(m, 'model_dump') else m for m in messages]
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
                    doc_types=classification,
                    tool_called=tool_name,
                    tool_input=tool_input,
                    raw_response={},
                    prompt_messages=[m.model_dump() if hasattr(m, 'model_dump') else m for m in messages],
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

        messages.extend(tool_result_messages)

        if _all_types_extracted(classification, extracted_records):
            break

    return extracted_records, classification


def _all_types_extracted(classifications: list, records: list)-> bool:
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


