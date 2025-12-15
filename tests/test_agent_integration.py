import unittest
from unittest.mock import MagicMock, patch
import os
import json
from kirosu.agent import KiroAgent

class TestAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.host = "127.0.0.1"
        self.port = 8765
        self.agent = KiroAgent(self.host, self.port, model="test-model")
        # Mock the client to avoid real network calls
        self.agent.client = MagicMock()
        self.agent.worker_id = "test-worker"

    @patch("subprocess.run")
    def test_tick_chat_task(self, mock_run):
        # Setup: Hub returns a task
        task = {
            "task_id": 123,
            "prompt": "Hello world",
            "type": "chat"
        }
        self.agent.client.call.side_effect = [
            {"tasks": [task]},  # Response to lease
            {"ok": True}        # Response to ack
        ]
        
        # Mock kiro-cli execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "AI Response"
        mock_run.return_value = mock_process

        # Execute one tick
        self.agent._tick()

        # Verify lease call
        self.agent.client.call.assert_any_call("lease", {
            "worker_id": "test-worker", 
            "max_tasks": 1, 
            "lease_seconds": 300
        })

        # Verify subprocess call (kiro-cli)
        mock_run.assert_called()
        args = mock_run.call_args[0][0]
        self.assertIn("kiro-cli", args)
        self.assertIn("Hello world", args[-1])

        # Verify ack call
        self.agent.client.call.assert_any_call("ack", {
            "task_id": 123,
            "status": "done",
            "result": "AI Response"
        })

    @patch("subprocess.run")
    def test_run_python_success(self, mock_run):
        # Setup task
        task = {
            "task_id": 456,
            "prompt": "print('hello')",
            "type": "python"
        }
        self.agent.client.call.side_effect = [
            {"tasks": [task]},
            {"ok": True}
        ]
        
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "hello\n"
        mock_run.return_value = mock_process

        self.agent._tick()
        
        # Verify python execution
        args = mock_run.call_args[0][0]
        self.assertIn("python3", args)
        self.assertIn("print('hello')", args)

    @patch("time.sleep")
    def test_run_loop_single_iteration(self, mock_sleep):
        # Make sleep raise an exception to exit the infinite loop
        mock_sleep.side_effect = KeyboardInterrupt
        
        # Mock tick to do nothing but ensure it's called
        with patch.object(self.agent, "_tick") as mock_tick:
            try:
                self.agent.run_loop(verbose=True)
            except KeyboardInterrupt:
                pass
            
            mock_tick.assert_called_once()

if __name__ == "__main__":
    unittest.main()
