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
        
        # Verify sheets and headers exist
        wb = openpyxl.load_workbook(output_path)
        self.assertIn("NA PDF", wb.sheetnames)
        self.assertIn("eChallan", wb.sheetnames)
        self.assertIn("Lease Deed", wb.sheetnames)
        
        # Verify NA PDF empty sheet
        ws_na = wb["NA PDF"]
        self.assertEqual(ws_na.max_row, 1)
        self.assertEqual(ws_na.cell(row=1, column=1).value, "Survey Number")

    def test_write_excel_with_data(self):
        output_path = os.path.join(self.output_dir, "data.xlsx")
        
        rows = [
            {
                "doc_type": "na_order",
                "survey_number": "123",
                "land_area": "1000",
                "source_file": "doc1.pdf"
            },
            {
                "doc_type": "echallan",
                "challan_number": "CH123",
                "amount": "500",
                "source_file": "doc2.pdf"
            },
            {
                "doc_type": "lease_deed",
                "dnr_number": "DNR999",
                "stamp_duty": "10000",
                "source_file": "doc3.pdf"
            }
        ]
        
        write_excel(rows, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        wb = openpyxl.load_workbook(output_path)
        
        # Check NA PDF Tab
        ws_na = wb["NA PDF"]
        self.assertEqual(ws_na.max_row, 2)
        self.assertEqual(ws_na.cell(row=2, column=1).value, "123")
        self.assertEqual(ws_na.cell(row=2, column=2).value, "1000")
        
        # Check eChallan Tab
        ws_echallan = wb["eChallan"]
        self.assertEqual(ws_echallan.max_row, 2)
        self.assertEqual(ws_echallan.cell(row=2, column=1).value, "CH123")
        self.assertEqual(ws_echallan.cell(row=2, column=4).value, "500")

        # Check Lease Deed Tab
        ws_lease = wb["Lease Deed"]
        self.assertEqual(ws_lease.max_row, 2)
        self.assertEqual(ws_lease.cell(row=2, column=1).value, "DNR999")
        
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
