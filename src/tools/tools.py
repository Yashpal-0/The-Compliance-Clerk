"""
Tool schemas for the Agent.
Schema enforcement happens HERE — the LLM is forced to populate
these exact fields. No JSON parsing gamble.
"""

TOOLS = [
    {
        "name": "classify_document",
        "description": (
            "ALWAYS call this first. Identify which document types are present "
            "in the provided text. A single PDF may contain multiple document types."
        ),
        "input_schema": {
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
                    "enum": ["english", "gujarati", "mixed"],
                    "description": "Primary language of the document"
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"]
                }
            },
            "required": ["doc_types_found", "language", "confidence"]
        }
    },
    {
        "name": "extract_na_order_fields",
        "description": (
            "Extract fields from an NA (Non-Agricultural) Permission Order. "
            "These are government orders from Prant Kacheri / Collector's office. "
            "Look for order numbers starting with iORA/, survey numbers, "
            "land area in sq.mt., and the signing authority."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "e.g. iORA/31/02/112/7/2026"
                },
                "application_number": {
                    "type": "string",
                    "description": "Application No. on the document"
                },
                "order_date": {
                    "type": "string",
                    "description": "Date of order in DD/MM/YYYY format"
                },
                "survey_number": {
                    "type": "string",
                    "description": "Survey/Block number of the land"
                },
                "village": {
                    "type": "string"
                },
                "taluka": {
                    "type": "string"
                },
                "district": {
                    "type": "string"
                },
                "land_area_sqm": {
                    "type": "number",
                    "description": "Land area in square meters (ચો.મી.)"
                },
                "lease_duration": {
                    "type": "string",
                    "description": "e.g. 28 years 11 months 0 days"
                },
                "purpose": {
                    "type": "string",
                    "description": "Purpose of NA permission e.g. Solar/Renewable Energy"
                },
                "lessee_name": {
                    "type": "string",
                    "description": "Company/person receiving the lease"
                },
                "authority_name": {
                    "type": "string",
                    "description": "Name of signing officer"
                },
                "authority_designation": {
                    "type": "string",
                    "description": "e.g. Prant Adhikari"
                }
            },
            "required": ["order_number", "order_date", "survey_number", 
                        "village", "land_area_sqm"]
        }
    },
    {
        "name": "extract_echallan_fields",
        "description": (
            "Extract fields from an e-Challan issued by Inspector General of "
            "Registration, Revenue Department, Government of Gujarat. "
            "A single PDF may have multiple challans (Registration Fee + Stamp Duty). "
            "Call this tool ONCE PER CHALLAN found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "application_number": {
                    "type": "string",
                    "description": "Application No (અરજી નંબર)"
                },
                "transaction_number": {
                    "type": "string",
                    "description": "Transaction No (ટ્રાન્ઝેક્શન નંબર)"
                },
                "account_head": {
                    "type": "string",
                    "description": "e.g. Registration Fee (0030-03-104-00) or Stamp Duty"
                },
                "amount": {
                    "type": "number",
                    "description": "Amount in INR"
                },
                "date": {
                    "type": "string",
                    "description": "Payment date DD-MM-YYYY"
                },
                "bank_branch": {
                    "type": "string"
                },
                "payee_name": {
                    "type": "string"
                },
                "office_name": {
                    "type": "string",
                    "description": "e.g. S.R.O - DHANERA"
                },
                "property_survey_no": {
                    "type": "string",
                    "description": "Survey number from Property Details"
                },
                "land_area_sqm": {
                    "type": "number"
                }
            },
            "required": ["transaction_number", "account_head", "amount", "date"]
        }
    },
    {
        "name": "extract_lease_deed_fields",
        "description": (
            "Extract fields from a registered Lease Deed document. "
            "Look for DNR number, lessor/lessee names, land area, "
            "lease term, registration date, and financial details."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "dnr_number": {
                    "type": "string",
                    "description": "Document Number from DNR box e.g. 838/2025"
                },
                "registration_date": {
                    "type": "string",
                    "description": "Date of registration DD/MM/YYYY"
                },
                "survey_number_new": {
                    "type": "string"
                },
                "survey_number_old": {
                    "type": "string"
                },
                "village": {
                    "type": "string"
                },
                "taluka": {
                    "type": "string"
                },
                "district": {
                    "type": "string"
                },
                "land_area_sqm": {
                    "type": "number"
                },
                "land_area_acres": {
                    "type": "number"
                },
                "lessor_name": {
                    "type": "string"
                },
                "lessee_name": {
                    "type": "string"
                },
                "lessee_cin": {
                    "type": "string"
                },
                "lease_term": {
                    "type": "string",
                    "description": "e.g. 29 years 11 months"
                },
                "consideration_price": {
                    "type": "number"
                },
                "stamp_duty": {
                    "type": "number"
                },
                "registration_fee": {
                    "type": "number"
                },
                "sub_registrar_office": {
                    "type": "string"
                }
            },
            "required": ["dnr_number", "registration_date", "survey_number_new",
                        "village", "land_area_sqm", "lessor_name", "lessee_name"]
        }
    },
    {
        "name": "flag_extraction_failure",
        "description": (
            "Call this if the document text is unreadable, too corrupted, "
            "or if required fields genuinely cannot be found. "
            "Do NOT guess or fabricate values — flag instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Why extraction failed"
                },
                "partial_data": {
                    "type": "object",
                    "description": "Any fields that WERE successfully extracted"
                }
            },
            "required": ["reason"]
        }
    }
]

# Tool names that produce extractable records
EXTRACTION_TOOLS = {
    "extract_na_order_fields",
    "extract_echallan_fields", 
    "extract_lease_deed_fields"
}