import os
import time
import unittest
from kirosu.db import TaskStore

class TestDBMetrics(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_metrics.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.store = TaskStore(self.db_path)

    def tearDown(self):
        self.store.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            if os.path.exists(self.db_path + "-wal"):
                os.remove(self.db_path + "-wal")
            if os.path.exists(self.db_path + "-shm"):
                os.remove(self.db_path + "-shm")

    def test_metrics_calculation(self):
        # Create some tasks
        t1 = self.store.enqueue("Task 1")
        t2 = self.store.enqueue("Task 2")
        t3 = self.store.enqueue("Task 3")
        
        # Lease and complete tasks
        tasks = self.store.lease("worker1", 1, 300)
        self.store.ack(tasks[0].task_id, "done", "res", None)
        
        tasks2 = self.store.lease("worker1", 1, 300)
        self.store.ack(tasks2[0].task_id, "failed", None, "err")

        # Check stats
        stats = self.store.stats()
        
        print(f"Stats: {stats}")
        
        self.assertEqual(stats["total_tasks"], 3)
        self.assertEqual(stats["queued"], 1)
        self.assertEqual(stats["done"], 1)
        self.assertEqual(stats["failed"], 1)
        
        # Verify derived metrics
        self.assertIn("avg_completion_time_sec", stats)
        self.assertIn("error_rate_percent", stats)
        self.assertEqual(stats["error_rate_percent"], 50.0) # 1 done, 1 failed
        self.assertGreaterEqual(stats["completed_last_hour"], 1)

if __name__ == "__main__":
    unittest.main()
