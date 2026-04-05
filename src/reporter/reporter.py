"""
Writes the final Excel output matching the required format.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from pathlib import Path

HEADERS = [
    "Sr.no.", "Village ", "Survey No.", "Area in NA Order",
    "Dated", "NA Order No.", "Lease Deed Doc. No.", "Lease Area ", "Lease Start "
]

HEADER_COLOR = "1F4E79"  # dark blue

def write_excel(rows: list[dict], output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    
    # Header row
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor=HEADER_COLOR)
    
    for col, header in enumerate(HEADERS, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    
    # Data rows
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, header in enumerate(HEADERS, 1):
            key = header.strip()
            value = row_data.get(key, "")
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Auto-size columns
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