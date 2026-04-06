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
    
    ws = wb.active
    ws.title = "Sheet1"
    headers = [
        "Sr.no.", "Village ", "Survey No.", "Area in NA Order", "Dated", 
        "NA Order No.", "Lease Deed Doc. No.", "Lease Area ", "Lease Start "
    ]
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor=HEADER_COLOR)
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        
    for row_idx, record in enumerate(records, 2):
        # We assume the records are already formatted by the linker to match the headers exactly
        for col_idx, header in enumerate(headers, 1):
            if header == "Sr.no.":
                ws.cell(row=row_idx, column=col_idx, value=row_idx - 1)
            else:
                ws.cell(row=row_idx, column=col_idx, value=record.get(header, ""))
            
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
    
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