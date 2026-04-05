import unittest
from unittest.mock import patch, MagicMock
from src.agent.agent import run_agent, _all_types_extracted

class TestAgent(unittest.TestCase):

    def test_all_type_extracted_true(self):
        classifications = ["echallan", "lease_deed"]
        records = [
            {"doc_type": "echallan"},
            {"doc_type": "lease_deed"}
        ]
        self.assertTrue(_all_types_extracted(classifications, records))

    def test_all_type_extracted_false(self):
        classifications = ["echallan", "lease_deed"]
        records = [
            {"doc_type": "echallan"}
        ]
        self.assertFalse(_all_types_extracted(classifications, records))

    def test_all_type_extracted_unknown(self):
        classifications = ["unknown"]
        records = [{"doc_type": "something"}]
        self.assertTrue(_all_types_extracted(classifications, records))

    def test_all_type_extracted_empty_records_with_unknown(self):
        classifications = ["unknown"]
        records = []
        self.assertFalse(_all_types_extracted(classifications, records))

    @patch('src.agent.agent.client.chat.completions.create')
    @patch('src.agent.agent.log_extraction')
    def test_run_agent_classify_and_stop(self, mock_log_extraction, mock_create):
        # Mocking the OpenAI response
        mock_response_1 = MagicMock()
        mock_response_1.choices = [MagicMock()]
        mock_response_1.choices[0].finish_reason = "tool_calls"
        mock_message_1 = MagicMock()
        mock_message_1.tool_calls = [MagicMock()]
        mock_message_1.tool_calls[0].function.name = "classify_document"
        mock_message_1.tool_calls[0].function.arguments = '{"doc_types_found": ["echallan"]}'
        mock_message_1.tool_calls[0].id = "call_123"
        mock_response_1.choices[0].message = mock_message_1

        mock_response_2 = MagicMock()
        mock_response_2.choices = [MagicMock()]
        mock_response_2.choices[0].finish_reason = "tool_calls"
        mock_message_2 = MagicMock()
        mock_message_2.tool_calls = [MagicMock()]
        mock_message_2.tool_calls[0].function.name = "extract_echallan_fields"
        mock_message_2.tool_calls[0].function.arguments = '{"account_head": "0030"}'
        mock_message_2.tool_calls[0].id = "call_456"
        mock_response_2.choices[0].message = mock_message_2

        # Side effect to return response 1 then response 2
        mock_create.side_effect = [mock_response_1, mock_response_2]

        with patch('src.agent.agent._all_types_extracted') as mock_all_extracted:
            mock_all_extracted.side_effect = [False, True]
            records, classifications = run_agent("dummy.pdf", "dummy text", ["echallan"])

        self.assertEqual(classifications, ["echallan"])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["doc_type"], "echallan")
        self.assertEqual(records[0]["account_head"], "0030")

    @patch('src.agent.agent.client.chat.completions.create')
    @patch('src.agent.agent.log_extraction')
    def test_run_agent_no_tool_calls(self, mock_log_extraction, mock_create):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_message = MagicMock()
        mock_message.tool_calls = None
        mock_response.choices[0].message = mock_message

        mock_create.return_value = mock_response

        with patch('src.agent.agent._all_types_extracted', return_value=False):
            records, classifications = run_agent("dummy.pdf", "empty text", [])

        self.assertEqual(len(records), 0)
        self.assertEqual(len(classifications), 0)

    def test_run_agent_actual_api_response(self):
        """Integration test that actually hits the OpenAI API"""
        print("\nRunning actual API integration test...")
        doc_text = """
        Traffic Police Gujarat
        e-Challan
        Challan No: CHGJ987654321
        Vehicle No: GJ-01-AB-1234
        Violation Date: 12-05-2023
        Offence: Over speeding
        Amount: 500
        Payment Status: Unpaid
        """
        records, classifications = run_agent("integration_test.pdf", doc_text, ["echallan"])
        
        print("Classifications found:", classifications)
        print("Records extracted:", records)
        
        self.assertIn("echallan", classifications)
        self.assertGreater(len(records), 0)
        self.assertEqual(records[0]["doc_type"], "echallan")

if __name__ == '__main__':
    unittest.main()
