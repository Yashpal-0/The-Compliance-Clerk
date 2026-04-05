import unittest
from src.linker.linker import (
    normalize,
    fuzzy_match,
    _find_matching_deed,
    link_records,
    build_output_row
)

class TestLinker(unittest.TestCase):

    def test_normalize(self):
        # Empty or None cases
        self.assertEqual(normalize(None), "")
        self.assertEqual(normalize(""), "")
        # String manipulations
        self.assertEqual(normalize(" Hello World "), "helloworld")
        self.assertEqual(normalize("MixEd CASE"), "mixedcase")
        self.assertEqual(normalize(123), "123")  # Numeric to string handle

    def test_fuzzy_match(self):
        # Exact match
        self.assertTrue(fuzzy_match("ahmedabad", "Ahmedabad"))
        # Close match over threshold (default 0.8)
        self.assertTrue(fuzzy_match("ahmedbad", "Ahmedabad")) 
        self.assertTrue(fuzzy_match("gandhinagar", "gandhinagr"))
        # Poor match below threshold
        self.assertFalse(fuzzy_match("surat", "rajkot"))

    def test_find_matching_deed_same_source(self):
        na_record = {"doc_type": "na_order", "source_file": "fileA.pdf"}
        lease_deeds = [
            {"doc_type": "lease_deed", "source_file": "fileB.pdf"},
            {"doc_type": "lease_deed", "source_file": "fileA.pdf"}
        ]
        
        # Priority 1: Should match the deed from the exact same source file
        match = _find_matching_deed(na_record, lease_deeds)
        self.assertIsNotNone(match)
        self.assertEqual(match["source_file"], "fileA.pdf")

    def test_find_matching_deed_village_and_survey(self):
        na_record = {"doc_type": "na_order", "source_file": "doc1.pdf", "village": "surat", "survey_number": "123"}
        lease_deeds = [
            {"doc_type": "lease_deed", "source_file": "doc2.pdf", "village": "vadodara", "survey_number_new": "123"},
            {"doc_type": "lease_deed", "source_file": "doc3.pdf", "village": "suraat", "survey_number_old": "123A"} # Fuzzy village + survey
        ]

        match = _find_matching_deed(na_record, lease_deeds)
        self.assertIsNotNone(match)
        self.assertEqual(match["source_file"], "doc3.pdf")

    def test_find_matching_deed_village_only(self):
        na_record = {"doc_type": "na_order", "source_file": "doc1.pdf", "village": "surat", "survey_number": "123"}
        lease_deeds = [
            {"doc_type": "lease_deed", "source_file": "doc2.pdf", "village": "vadodara", "survey_number_new": "456"},
            {"doc_type": "lease_deed", "source_file": "doc3.pdf", "village": "suraat", "survey_number_new": "789"} # Only fuzzy village matches
        ]

        match = _find_matching_deed(na_record, lease_deeds)
        self.assertIsNotNone(match)
        self.assertEqual(match["source_file"], "doc3.pdf")

    def test_find_matching_deed_no_match(self):
        na_record = {"doc_type": "na_order", "source_file": "doc1.pdf", "village": "surat", "survey_number": "123"}
        lease_deeds = [
            {"doc_type": "lease_deed", "source_file": "doc2.pdf", "village": "vadodara", "survey_number_new": "456"}
        ]
        match = _find_matching_deed(na_record, lease_deeds)
        self.assertIsNone(match)

    def test_build_output_row(self):
        na_record = {
            "village": "Test Village",
            "survey_number": "100",
            "land_area_sqm": "500",
            "order_date": "01/01/2026",
            "order_number": "NA/100"
        }
        lease_record = {
            "village": "Test Village",
            "dnr_number": "DNR/200",
            "land_area_sqm": "500",
            "registration_date": "01/02/2026"
        }
        challans = []
        
        # Test full population
        row = build_output_row(na_record, lease_record, challans, sr_no=1)
        self.assertEqual(row["Sr.no."], 1)
        self.assertEqual(row["Village"], "Test Village")
        self.assertEqual(row["Survey No."], "100")
        self.assertEqual(row["Lease Deed Doc. No."], "DNR/200")
        
        # Test fallback population
        row_lease_only = build_output_row(None, lease_record, challans, sr_no=2)
        self.assertEqual(row_lease_only["Village"], "Test Village") # uses lease village

    def test_link_records(self):
        records = [
            {"doc_type": "na_order", "source_file": "f1.pdf", "village": "surat", "survey_number": "11", "order_number": "NA1"},
            {"doc_type": "lease_deed", "source_file": "f1.pdf", "village": "surat", "dnr_number": "DEED1"},
            {"doc_type": "echallan", "source_file": "f1.pdf", "account_head": "0030"}, # attached to f1 deed
            {"doc_type": "lease_deed", "source_file": "f2.pdf", "village": "vadodara", "dnr_number": "DEED2"}, # Standalone Deed
            {"doc_type": "na_order", "source_file": "f3.pdf", "village": "rajkot", "survey_number": "33"} # Standalone NA Order
        ]

        merged = link_records(records)
        
        # We expect 3 total output rows: 
        # 1 combined (f1.pdf), 1 standalone NA order (f3.pdf), 1 standalone deed (f2.pdf)
        self.assertEqual(len(merged), 3)

        # Check combined record (matches first on source file)
        self.assertEqual(merged[0]["Sr.no."], 1)
        self.assertEqual(merged[0]["NA Order No."], "NA1")
        self.assertEqual(merged[0]["Lease Deed Doc. No."], "DEED1")
        
        # Check standalone NA order
        self.assertEqual(merged[1]["Sr.no."], 2)
        self.assertEqual(merged[1]["Village"], "rajkot")
        self.assertEqual(merged[1]["Lease Deed Doc. No."], "")
        
        # Check standalone lease deed
        self.assertEqual(merged[2]["Sr.no."], 3)
        self.assertEqual(merged[2]["Village"], "vadodara")
        self.assertEqual(merged[2]["NA Order No."], "")


if __name__ == '__main__':
    unittest.main()
