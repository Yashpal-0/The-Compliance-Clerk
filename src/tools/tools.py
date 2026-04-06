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
                    "survey_no": {"type": "string"},
                    "village": {"type": "string"},
                    "na_order_no": {
                        "type": "string",
                        "description": "NA Order Number, often starting with iORA/"
                    },
                    "area_in_na_order": {
                        "type": "string",
                        "description": "Land area mentioned in the order (e.g., in sq.mt. or acres)"
                    },
                    "owner_name": {"type": "string"},
                    "dated": {
                        "type": "string",
                        "description": "Date in DD/MM/YYYY format"
                    },
                    "authority_details": {
                        "type": "string",
                        "description": "Name and designation of authority issuing the order"
                    }
                },
                "required": ["survey_no", "village", "na_order_no", "area_in_na_order", "owner_name", "dated", "authority_details"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_echallan_fields",
            "description": (
                "Extract fields ONLY from an eChallan for TRAFFIC VIOLATIONS ONLY. "
                "DO NOT call this tool for Stamp Duty or Registration Fee receipts. "
                "Look for Vehicle Number and Violation details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "challan_number": {"type": "string"},
                    "vehicle_number": {"type": "string"},
                    "violation_date": {"type": "string"},
                    "amount": {"type": "string"},
                    "offence_description": {"type": "string"},
                    "payment_status": {"type": "string"}
                },
                "required": ["challan_number", "vehicle_number", "violation_date", "amount", "offence_description", "payment_status"]
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
                    "lease_deed_doc_no": {
                        "type": "string",
                        "description": "e.g. 838/2025"
                    },
                    "lease_start": {"type": "string"},
                    "survey_no_new": {"type": "string"},
                    "survey_no_old": {"type": "string"},
                    "village": {"type": "string"},
                    "taluka": {"type": "string"},
                    "district": {"type": "string"},
                    "lease_area": {"type": "string"},
                    "land_area_acres": {"type": "string"},
                    "lessor_name": {"type": "string"},
                    "lessee_name": {"type": "string"},
                    "lessee_cin": {"type": "string"},
                    "lease_term": {"type": "string"},
                    "consideration_price": {"type": "string"},
                    "stamp_duty": {"type": "string"},
                    "registration_fee": {"type": "string"},
                    "sub_registrar_office": {"type": "string"}
                },
                "required": ["lease_deed_doc_no", "lease_start", "survey_no_new",
                             "village", "lease_area", "lessor_name", "lessee_name"]
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