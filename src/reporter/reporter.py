"""
Writes the final Excel output matching the required format.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from pathlib import Path

HEADER_COLOR = "1F4E79"  # dark blue

def write_excel(records: list[dict], output_path: str):
    wb = openpyxl.Workbook()
    
    # Collect separate types
    echallans = [r for r in records if r.get("doc_type") == "echallan"]
    na_orders = [r for r in records if r.get("doc_type") == "na_order"]
    lease_deeds = [r for r in records if r.get("doc_type") == "lease_deed"]
    
    # Setup NA PDF sheet
    ws_na = wb.active
    ws_na.title = "NA PDF"
    na_headers = ["Survey Number", "Land Area", "Owner Name", "Order Date", "Authority Details", "Source File"]
    
    # Setup eChallan sheet
    ws_echallan = wb.create_sheet(title="eChallan")
    echallan_headers = ["Challan Number", "Vehicle Number", "Violation Date", "Amount", "Offence Description", "Payment Status", "Source File"]

    # Setup Lease Deed sheet
    ws_lease_deed = wb.create_sheet(title="Lease Deed")
    lease_deed_headers = ["DNR Number", "Registration Date", "Survey Number (New)", "Village", "Land Area (SQM)", "Lessor Name", "Lessee Name", "Consideration Price", "Stamp Duty", "Registration Fee", "Source File"]

    def _write_sheet(ws, headers, data, key_map):
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill("solid", fgColor=HEADER_COLOR)
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
            
        for row_idx, row_data in enumerate(data, 2):
            for col_idx, key in enumerate(key_map, 1):
                ws.cell(row=row_idx, column=col_idx, value=row_data.get(key, ""))
                
        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    # Write data mappings
    na_keys = ["survey_number", "land_area", "owner_name", "order_date", "authority_details", "source_file"]
    echallan_keys = ["challan_number", "vehicle_number", "violation_date", "amount", "offence_description", "payment_status", "source_file"]
    lease_deed_keys = ["dnr_number", "registration_date", "survey_number_new", "village", "land_area_sqm", "lessor_name", "lessee_name", "consideration_price", "stamp_duty", "registration_fee", "source_file"]

    _write_sheet(ws_na, na_headers, na_orders, na_keys)
    _write_sheet(ws_echallan, echallan_headers, echallans, echallan_keys)
    _write_sheet(ws_lease_deed, lease_deed_headers, lease_deeds, lease_deed_keys)
    
    wb.save(output_path)
    print(f"✓ Excel saved → {output_path}")


def write_failed_log(failed: list[dict], output_dir: str):
    """Write a separate sheet for files that failed extraction."""
    if not failed:
        return
    path = Path(output_dir) / "failed_extractions.txt"
    with open(path, "w") as f:
        for item in failed:
            f.write(f"{item['file']}: {item['reason']}\n")