import unittest
import sqlite3
import os
import json
from audit import init_db, log_extraction, log_run_summary
import audit

class TestAuditLog(unittest.TestCase):
    def setUp(self):
        # Override the DB_PATH to use a test database file
        self.test_db = "test_audit.db"
        audit.DB_PATH = self.test_db
        # Initialize the test schema
        init_db()

    def tearDown(self):
        # Clean up the test database after each test
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_init_db(self):
        """Test that tables are successfully created."""
        with sqlite3.connect(self.test_db) as conn:
            # Check if extraction_logs table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='extraction_logs'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check if run_summary table exists
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='run_summary'")
            self.assertIsNotNone(cursor.fetchone())

    def test_log_extraction(self):
        """Test inserting a log into the extraction_logs table."""
        test_file = "sample.pdf"
        test_method = "pdfplumber"
        test_types = ["lease_deed"]
        test_tool = "extract_lease_deed_fields"
        test_input = {"file": "sample.pdf"}
        test_response = {"status": "ok", "dnr_number": "123"}
        
        log_extraction(
            source_file=test_file,
            extraction_method=test_method,
            doc_types=test_types,
            tool_called=test_tool,
            tool_input=test_input,
            raw_response=test_response
        )
        
        with sqlite3.connect(self.test_db) as conn:
            cursor = conn.execute("SELECT source_file, doc_types_detected, raw_response FROM extraction_logs")
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], test_file)
            self.assertEqual(json.loads(row[1]), test_types)
            self.assertEqual(json.loads(row[2]), test_response)

    def test_log_run_summary(self):
        """Test inserting a summary into the run_summary table."""
        log_run_summary(
            total=10,
            successful=8,
            failed=2,
            output_file="output.xlsx"
        )
        
        with sqlite3.connect(self.test_db) as conn:
            cursor = conn.execute("SELECT total_files, successful, failed, output_file FROM run_summary")
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[0], 10)
            self.assertEqual(row[1], 8)
            self.assertEqual(row[2], 2)
            self.assertEqual(row[3], "output.xlsx")

if __name__ == "__main__":
    unittest.main()
