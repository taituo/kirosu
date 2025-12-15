import unittest
from unittest.mock import patch, MagicMock
from kirosu.strategy import suggest_strategy, TOPOLOGIES

class TestStrategy(unittest.TestCase):
    @patch("subprocess.run")
    def test_suggest_strategy_success(self, mock_run):
        # Mock the subprocess output
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = '{"topology": "parallel", "reasoning": "Tasks are independent", "command": "kirosu run-agent"}'
        mock_run.return_value = mock_process

        result = suggest_strategy("Process 100 files")
        
        self.assertEqual(result["topology"], "parallel")
        self.assertIn("Process 100 files", str(mock_run.call_args))
        
    @patch("subprocess.run")
    def test_suggest_strategy_failure(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.stderr = "Error details"
        mock_run.return_value = mock_process
        
        result = suggest_strategy("Task")
        self.assertEqual(result["topology"], "single") # Fallback
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()
