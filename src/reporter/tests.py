import unittest
import tempfile
import os
from pathlib import Path
import openpyxl

from src.reporter.reporter import write_excel, write_failed_log

class TestReporter(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for output files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name

    def tearDown(self):
        # Clean up the temporary directory
        self.temp_dir.cleanup()

    def test_write_excel_empty_rows(self):
        output_path = os.path.join(self.output_dir, "empty.xlsx")
        
        # Test with empty rows
        write_excel([], output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        # Verify only headers exist
        wb = openpyxl.load_workbook(output_path)
        ws = wb.active
        self.assertEqual(ws.max_row, 1)
        self.assertEqual(ws.max_column, len(HEADERS))
        
        for col, header in enumerate(HEADERS, 1):
            cell = ws.cell(row=1, column=col)
            self.assertEqual(cell.value, header)
            self.assertEqual(cell.font.bold, True)
            self.assertEqual(cell.font.color.rgb, "00FFFFFF")

    def test_write_excel_with_data(self):
        output_path = os.path.join(self.output_dir, "data.xlsx")
        
        rows = [
            {
                "Sr.no.": 1,
                "Village": "Surat",
                "Survey No.": "123",
                "Area in NA Order": "1000",
                "Dated": "12/12/2026",
                "NA Order No.": "NA123",
                "Lease Deed Doc. No.": "DNR123",
                "Lease Area": "500",
                "Lease Start": "01/01/2027",
                "ExtraKey": "This should be ignored"
            },
            {
                # Missing keys should be replaced by empty strings
                "Sr.no.": 2,
                "Village": "Rajkot"
            }
        ]
        
        write_excel(rows, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        wb = openpyxl.load_workbook(output_path)
        ws = wb.active
        self.assertEqual(ws.max_row, 3)
        
        # Check first row of data (Row 2 in Excel)
        self.assertEqual(ws.cell(row=2, column=1).value, 1)
        self.assertEqual(ws.cell(row=2, column=2).value, "Surat")
        self.assertEqual(ws.cell(row=2, column=3).value, "123")
        
        # Check second row of data (Row 3 in Excel)
        self.assertEqual(ws.cell(row=3, column=1).value, 2)
        self.assertEqual(ws.cell(row=3, column=2).value, "Rajkot")
        self.assertIn(ws.cell(row=3, column=3).value, ["", None]) # Openpyxl reads empty string cells as None
        
        # Check that auto-sizing worked
        self.assertGreater(ws.column_dimensions['A'].width, 0)

    def test_write_failed_log_empty(self):
        # Empty array means no file should be created
        write_failed_log([], self.output_dir)
        log_path = Path(self.output_dir) / "failed_extractions.txt"
        self.assertFalse(log_path.exists())

    def test_write_failed_log_with_data(self):
        failed_list = [
            {"file": "missing.pdf", "reason": "No text found"},
            {"file": "corrupt.pdf", "reason": "Decryption error"}
        ]
        
        write_failed_log(failed_list, self.output_dir)
        log_path = Path(self.output_dir) / "failed_extractions.txt"
        self.assertTrue(log_path.exists())
        
        with open(log_path, "r") as f:
            content = f.read()
            
        self.assertIn("missing.pdf: No text found", content)
        self.assertIn("corrupt.pdf: Decryption error", content)

if __name__ == '__main__':
    unittest.main()
