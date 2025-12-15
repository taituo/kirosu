import unittest
import os
import threading
import time
from kirosu.hub import run_hub, _HubState
from kirosu.db import TaskStore
from kirosu.agent import HubClient

class TestHITL(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_hitl.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        # Start a hub in a thread
        self.port = 8799
        self.hub_thread = threading.Thread(target=run_hub, args=(self.db_path, "127.0.0.1", self.port, 300))
        self.hub_thread.daemon = True
        self.hub_thread.start()
        time.sleep(1) # Wait for hub startup

    def tearDown(self):
        # Shutdown hub via client
        try:
            client = HubClient("127.0.0.1", self.port)
            client.call("shutdown")
        except:
            pass
            
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            if os.path.exists(self.db_path + "-wal"): os.remove(self.db_path + "-wal")
            if os.path.exists(self.db_path + "-shm"): os.remove(self.db_path + "-shm")

    def test_approval_flow(self):
        client = HubClient("127.0.0.1", self.port)
        
        # 1. Enqueue a task
        resp = client.call("enqueue", {"prompt": "Approval Request", "type": "human"})
        task_id = resp["task_id"]
        
        # 2. Verify status is queued (normally agent would pick it up, but here we treat it as waiting for human)
        # In a real workflow, the 'Planner' might wait for this task to be 'done'.
        
        # 3. Approve via API/CLI
        client.call("approve", {"task_id": task_id})
        
        # 4. Verify status is done
        list_resp = client.call("list", {"limit": 1})
        task = list_resp["tasks"][0]
        
        self.assertEqual(task["task_id"], task_id)
        self.assertEqual(task["status"], "done")
        self.assertIn("Approved by human", task["result"])

if __name__ == "__main__":
    unittest.main()
