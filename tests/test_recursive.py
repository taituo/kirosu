import unittest
from unittest.mock import patch, MagicMock
import os
from kirosu.strategy import RecursiveStrategy

class TestRecursiveStrategy(unittest.TestCase):
    @patch("subprocess.run")
    def test_execute_success(self, mock_run):
        # Mock planner output
        planner_process = MagicMock()
        planner_process.returncode = 0
        planner_process.stdout = """
pipeline:
  - id: step_1
    module: agents.worker
"""
        # Mock execution output
        exec_process = MagicMock()
        exec_process.returncode = 0
        
        mock_run.side_effect = [planner_process, exec_process]

        RecursiveStrategy.execute("Build a website")
        
        # Check if plan file was created
        self.assertTrue(os.path.exists("recursive_plan.yml"))
        with open("recursive_plan.yml") as f:
            content = f.read()
            self.assertIn("pipeline:", content)
            
        # Verify subprocess calls
        # 1. Planner call
        self.assertIn("kiro-cli", str(mock_run.call_args_list[0]))
        # 2. Execution call
        self.assertIn("run-pipeline", str(mock_run.call_args_list[1]))
        
        # Cleanup
        if os.path.exists("recursive_plan.yml"):
            os.remove("recursive_plan.yml")

if __name__ == "__main__":
    unittest.main()
