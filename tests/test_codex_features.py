import unittest
from unittest.mock import patch, MagicMock
import os
import json
from kirosu.strategy import suggest_strategy, RecursiveStrategy
from kirosu.providers import CodexProvider

class TestCodexFeatures(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {
            "KIRO_PROVIDER": "codex",
            "MITTELO_KIRO_MODEL": "gpt-5.1-codex-mini"
        })
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("subprocess.run")
    def test_suggest_strategy_with_codex(self, mock_run):
        """Verify kirosu suggest uses CodexProvider correctly"""
        # Mock LLM Output
        mock_response = json.dumps({
            "topology": "parallel",
            "reasoning": "Codex says parallel is best.",
            "command": "kirosu run-pipeline ..."
        })
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = mock_response
        mock_run.return_value = mock_process

        # Run
        result = suggest_strategy("Process 100 files")

        # Verify Code Logic
        self.assertEqual(result["topology"], "parallel")
        
        # Verify Provider Usage
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        
        self.assertIn("codex", cmd)
        self.assertIn("exec", cmd) # Must use exec subcommand
        self.assertIn("--dangerously-bypass-approvals-and-sandbox", cmd)
        self.assertIn("gpt-5.1-codex-mini", cmd)
        self.assertIn("Process 100 files", cmd[-1])

    @patch("subprocess.run")
    def test_recursive_planning_with_codex(self, mock_run):
        """Verify kirosu run-recursive uses CodexProvider for planning"""
        # Mock Planner Output
        mock_yaml = """
        pipeline:
          - id: step1
            module: agents.worker
        """
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = mock_yaml
        mock_run.return_value = mock_process

        # We also need to mock the *execution* phase of recursive strategy
        # RecursiveStrategy calls subprocess.run(["kirosu", "run-pipeline"...]) at the end.
        # We can mock subprocess.run to handle both calls.
        
        def side_effect(cmd, **kwargs):
            if "codex" in cmd:
                # This is the planning call
                return mock_process
            elif "kirosu" in cmd and "run-pipeline" in cmd:
                # This is the execution call
                exec_mock = MagicMock()
                exec_mock.returncode = 0
                return exec_mock
            return MagicMock()

        mock_run.side_effect = side_effect

        # Run
        # We mock open() to avoid writing files
        with patch("builtins.open", unittest.mock.mock_open()):
             RecursiveStrategy.execute("Build a rocket")

        # Verify Calls
        # Should have called Codex once for planning
        # Should have called kirosu run-pipeline once for execution
        
        codex_called = False
        pipeline_called = False
        
        for call in mock_run.call_args_list:
            args = call[0][0]
            if "codex" in args:
                codex_called = True
                self.assertIn("exec", args)
                self.assertIn("gpt-5.1-codex-mini", args)
            if "run-pipeline" in args:
                pipeline_called = True
                
        self.assertTrue(codex_called, "Codex should be called for planning")
        self.assertTrue(pipeline_called, "Pipeline execution should be triggered")

if __name__ == "__main__":
    unittest.main()
