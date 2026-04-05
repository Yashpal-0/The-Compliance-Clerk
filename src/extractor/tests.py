import unittest
import os
import shutil
from src.extractor.extractor import extract_text, detect_doc_type

class TestExtractor(unittest.TestCase):
    def setUp(self):
        # Base path for PDF files
        self.files_dir = "Files"
        self.sample_pdf = os.path.join(self.files_dir, "256 FINAL ORDER.pdf")
        self.lease_pdf = os.path.join(self.files_dir, "Rampura Mota S.No.- 251p2 Lease Deed No.- 141.pdf")

    def test_detect_doc_type_echallan(self):
        text = "This is an E-Challan for registration fee payment."
        result = detect_doc_type(text)
        self.assertIn("echallan", result)

    def test_detect_doc_type_lease_deed(self):
        text = "Agreement for Lease Deed between lessor and lessee."
        result = detect_doc_type(text)
        self.assertIn("lease_deed", result)

    def test_detect_doc_type_na_order(self):
        text = "The non-agricultural order (NA order) was issued by Prant Adhikari."
        result = detect_doc_type(text)
        self.assertIn("na_order", result)

    def test_detect_doc_type_unknown(self):
        text = "Generic document with no keywords."
        result = detect_doc_type(text)
        self.assertEqual(result, ["unknown"])

    def test_extract_text_integration(self):
        """Integration test for all PDF files in the Files directory."""
        if shutil.which("tesseract") is None:
            self.skipTest("Tesseract OCR is not installed. Skipping integration test.")

        if not os.path.exists(self.files_dir):
            self.skipTest(f"Directory {self.files_dir} not found.")

        pdf_files = [f for f in os.listdir(self.files_dir) if f.lower().endswith('.pdf')]
        
        # Limit to 1 file to prevent long-running test suites parsing massive PDFs
        pdf_files = pdf_files[:1]

        if not pdf_files:
            self.skipTest(f"No PDF files found in {self.files_dir}.")

        for pdf_file in pdf_files:
            with self.subTest(pdf_file=pdf_file):
                pdf_path = os.path.join(self.files_dir, pdf_file)
                text, method = extract_text(pdf_path)
                
                self.assertIsInstance(text, str, f"Failed for {pdf_file}")
                self.assertGreater(len(text), 0, f"No text extracted for {pdf_file}")
                self.assertIn(method, ["pdfplumber", "ocr"], f"Unknown method for {pdf_file}")
                
                # Test detection on the extracted text
                doc_types = detect_doc_type(text)
                self.assertIsInstance(doc_types, list, f"Invalid doc_types for {pdf_file}")
                print(f"File: {pdf_file} | Method: {method} | Types: {doc_types}")

if __name__ == "__main__":
    unittest.main()
