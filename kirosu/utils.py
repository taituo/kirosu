import os
from typing import Generator, Any
from .hub import HubClient

class TaskSplitter:
    """Helper to split large jobs into smaller tasks."""
    
    def __init__(self, hub_host: str, hub_port: int):
        self.client = HubClient(hub_host, hub_port)

    def split_and_enqueue(self, items: list[Any], prompt_template: str, batch_size: int = 1, task_type: str = "chat") -> list[int]:
        """
        Split a list of items into tasks and enqueue them.
        
        Args:
            items: List of data items to process.
            prompt_template: String with {item} placeholder.
            batch_size: Number of items per task (simple concatenation).
            task_type: "chat" or "python".
            
        Returns:
            List of enqueued task IDs.
        """
        task_ids = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            # Simple joining for batching, can be customized
            batch_content = "\n---\n".join(str(item) for item in batch)
            prompt = prompt_template.format(item=batch_content)
            
            resp = self.client.call("enqueue", {
                "prompt": prompt,
                "type": task_type
            })
            task_ids.append(resp["task_id"])
            
        return task_ids

    def wait_for_completion(self, task_ids: list[int], poll_interval: float = 1.0) -> dict[int, Any]:
        """Wait for a specific set of tasks to complete."""
        import time
        results = {}
        pending = set(task_ids)
        
        while pending:
            # In a real massive system, we wouldn't poll list() like this, 
            # but for <1000 tasks it's okay. Better would be get_task(id).
            # We'll use list with a large limit for now.
            resp = self.client.call("list", {"limit": 1000, "status": "done"})
            done_tasks = {t["task_id"]: t for t in resp.get("tasks", [])}
            
            for tid in list(pending):
                if tid in done_tasks:
                    results[tid] = done_tasks[tid]
                    pending.remove(tid)
            
            if pending:
                time.sleep(poll_interval)
                
        return results
