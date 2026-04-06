"""
Links NA Orders to their corresponding Lease Deeds.
Matching key: (village, survey_number)
This produces the final merged row matching the output Excel format.
"""
from difflib import SequenceMatcher


def normalize(val: str) -> str:
    if not val:
        return ""
    return str(val).strip().lower().replace(" ", "")


def fuzzy_match(a: str, b: str, threshold: float = 0.8) -> bool:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio() >= threshold

def _find_matching_deed(na_record: dict, lease_deeds: list[dict])-> dict | None:
    """
    Find the lease deed that matches a given NA order.
    Matching logic (in order of priority):
    1. Same survey number (Foreign Key)
    2. Same source file (bundled PDF)
    3. Same village (fuzzy)
    """
    
    na_village = na_record.get("village", "")
    na_survey = normalize(na_record.get("survey_no", ""))
    na_file = na_record.get("source_file", "")

    # Priority 1: Survey Number match (Foreign Key)
    for deed in lease_deeds:
        survey_new = normalize(deed.get("survey_no_new", ""))
        survey_old = normalize(deed.get("survey_no_old", ""))
        if na_survey and (na_survey in survey_new or na_survey in survey_old or survey_new in na_survey):
            return deed

    # Priority 2: same PDF file
    for deed in lease_deeds:
        if na_file and deed.get("source_file") == na_file:
            return deed
        
    # Priority 3: village match only (weaker)
    for deed in lease_deeds:
        if na_village and fuzzy_match(na_village, deed.get("village", "")):
            return deed

    return None
        




def link_records(all_records: list[dict])-> list[dict]:
    """
    Produces output rows. Logic:
    
    - Each NA Order = one output row
    - Matched to its Lease Deed by (village, survey_no)
    - e-Challans are attached to Lease Deeds (Registration Fee + Stamp Duty)
    - If a Lease Deed has no matching NA Order → still gets its own row
    - Unmatched e-Challans → separate rows flagged as standalone
    """

    na_orders = [r for r in all_records if r["doc_type"]=="na_order"]
    lease_deeds = [r for r in all_records if r["doc_type"]=="lease_deed"]
    echallans  = [r for r in all_records if r["doc_type"] == "echallan"]


    merged_rows = []
    used_deed_ids = set()

    for na in na_orders:
        matched_deed = _find_matching_deed(na, lease_deeds)
        matched_challans = []

        if matched_deed:
            deed_id = id(matched_deed)
            used_deed_ids.add(deed_id)

            matched_challans = [
                c for c in echallans
                if c.get("source_file") == matched_deed.get("source_file")
            ]
            
        merged_rows.append(
            build_output_row(na, matched_deed, matched_challans, len(merged_rows)+1)
        )

    for deed in lease_deeds:
        if id(deed) not in used_deed_ids:
            matched_challans = [
                c for c in echallans
                if c.get("source_file") == deed.get("source_file")
            ]

            merged_rows.append(
                build_output_row(None, deed, matched_challans, len(merged_rows)+1)
            )
    return merged_rows


def build_output_row(
        na_record: dict | None,
        lease_record: dict | None,
        challans: list[dict], 
        sr_no: int
)-> dict:
    na_village = str(na_record.get("village", "")).strip() if na_record else ""
    lease_village = str(lease_record.get("village", "")).strip() if lease_record else ""
    final_village = na_village or lease_village

    # If survey number matched, but they yielded different village names,
    # preferentially choose the English one (ASCII).
    if na_village and lease_village and na_village != lease_village:
        if lease_village.isascii() and not na_village.isascii():
            final_village = lease_village
        elif na_village.isascii() and not lease_village.isascii():
            final_village = na_village

    row = {
        "Sr.no.": sr_no,
        "Village ": final_village,
        "Survey No.": "",
        "Area in NA Order": "",
        "Dated": "",
        "NA Order No.": "",
        "Lease Deed Doc. No.": "",
        "Lease Area ": "",
        "Lease Start ": "",
    }

    if na_record:
        row["Survey No."]       = na_record.get("survey_no", "")
        row["Area in NA Order"] = na_record.get("area_in_na_order", "")
        row["Dated"]            = na_record.get("dated", "")
        row["NA Order No."]     = na_record.get("na_order_no", "")

    if lease_record:
        row["Lease Deed Doc. No."] = lease_record.get("lease_deed_doc_no", "")
        row["Lease Area "]         = lease_record.get("lease_area", "")
        row["Lease Start "]        = lease_record.get("lease_start", "")
        # Fallback survey if NA order missing
        if not row["Survey No."]:
            row["Survey No."] = lease_record.get("survey_no_new", "")

    return row
