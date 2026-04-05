# src/tools.py

TOOLS = [
    {
        "type": "function",                      # OpenAI requires this wrapper
        "function": {
            "name": "classify_document",
            "description": (
                "ALWAYS call this first. Identify which document types are present "
                "in the provided text. A single PDF may contain multiple document types."
            ),
            "parameters": {                      # 'parameters' not 'input_schema'
                "type": "object",
                "properties": {
                    "doc_types_found": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["na_order", "echallan", "lease_deed", "unknown"]
                        },
                        "description": "All document types found. Can have multiple values."
                    },
                    "language": {
                        "type": "string",
                        "enum": ["english", "gujarati", "mixed"]
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"]
                    }
                },
                "required": ["doc_types_found", "language", "confidence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_na_order_fields",
            "description": (
                "Extract fields from an NA (Non-Agricultural) Permission Order. "
                "These are government orders from Prant Kacheri / Collector's office. "
                "Look for order numbers starting with iORA/, survey numbers, "
                "land area in sq.mt., and the signing authority."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "e.g. iORA/31/02/112/7/2026"
                    },
                    "application_number": {"type": "string"},
                    "order_date": {
                        "type": "string",
                        "description": "Date in DD/MM/YYYY format"
                    },
                    "survey_number": {"type": "string"},
                    "village": {"type": "string"},
                    "taluka": {"type": "string"},
                    "district": {"type": "string"},
                    "land_area_sqm": {
                        "type": "number",
                        "description": "Land area in square meters"
                    },
                    "lease_duration": {"type": "string"},
                    "purpose": {"type": "string"},
                    "lessee_name": {"type": "string"},
                    "authority_name": {"type": "string"},
                    "authority_designation": {"type": "string"}
                },
                "required": ["order_number", "order_date", "survey_number",
                             "village", "land_area_sqm"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_echallan_fields",
            "description": (
                "Extract fields from an e-Challan issued by Inspector General of "
                "Registration, Revenue Department, Government of Gujarat. "
                "Call this ONCE PER CHALLAN — a PDF may have multiple challans."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "application_number": {"type": "string"},
                    "transaction_number": {"type": "string"},
                    "account_head": {
                        "type": "string",
                        "description": "e.g. Registration Fee or Stamp Duty"
                    },
                    "amount": {"type": "number"},
                    "date": {"type": "string"},
                    "bank_branch": {"type": "string"},
                    "payee_name": {"type": "string"},
                    "office_name": {"type": "string"},
                    "property_survey_no": {"type": "string"},
                    "land_area_sqm": {"type": "number"}
                },
                "required": ["transaction_number", "account_head", "amount", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_lease_deed_fields",
            "description": (
                "Extract fields from a registered Lease Deed. "
                "Look for DNR number, lessor/lessee names, land area, "
                "lease term, registration date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dnr_number": {
                        "type": "string",
                        "description": "e.g. 838/2025"
                    },
                    "registration_date": {"type": "string"},
                    "survey_number_new": {"type": "string"},
                    "survey_number_old": {"type": "string"},
                    "village": {"type": "string"},
                    "taluka": {"type": "string"},
                    "district": {"type": "string"},
                    "land_area_sqm": {"type": "number"},
                    "land_area_acres": {"type": "number"},
                    "lessor_name": {"type": "string"},
                    "lessee_name": {"type": "string"},
                    "lessee_cin": {"type": "string"},
                    "lease_term": {"type": "string"},
                    "consideration_price": {"type": "number"},
                    "stamp_duty": {"type": "number"},
                    "registration_fee": {"type": "number"},
                    "sub_registrar_office": {"type": "string"}
                },
                "required": ["dnr_number", "registration_date", "survey_number_new",
                             "village", "land_area_sqm", "lessor_name", "lessee_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_extraction_failure",
            "description": (
                "Call if the document is unreadable or fields cannot be found. "
                "Never fabricate — flag instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "partial_data": {"type": "object"}
                },
                "required": ["reason"]
            }
        }
    }
]

# Tool names that produce extractable records (no wrapper needed here)
EXTRACTION_TOOLS = {
    "extract_na_order_fields",
    "extract_echallan_fields",
    "extract_lease_deed_fields"
}