import pytest
import time
import threading
import random
from kiro_swarm.agent import KiroAgent, HubClient

def test_concurrency(hub_port):
    """
    Test that multiple agents can process tasks concurrently without race conditions.
    """
    client = HubClient("127.0.0.1", hub_port)
    
    # Enqueue multiple tasks
    num_tasks = 20
    print(f"Enqueuing {num_tasks} tasks...")
    for i in range(num_tasks):
        client.call("enqueue", {"prompt": f"echo 'Task {i}'"})
        
    # Start multiple agents
    num_workers = 5
    agents = []
    stop_event = threading.Event()
    
    print(f"Starting {num_workers} agents...")
    
    def agent_loop(worker_idx):
        # Each agent gets a unique ID implicitly, but we can also force one if needed.
        # KiroAgent generates a random ID on init.
        agent = KiroAgent("127.0.0.1", hub_port)
        # Add a small random delay to start to simulate staggered startup
        time.sleep(random.random() * 0.5)
        
        while not stop_event.is_set():
            try:
                agent._tick()
            except Exception as e:
                print(f"Worker {worker_idx} error: {e}")
            time.sleep(0.1)

    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=agent_loop, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        
    # Wait for all tasks to be done
    start = time.time()
    timeout = 30 # Should be plenty for 20 simple echo tasks with 5 workers
    
    while time.time() - start < timeout:
        stats = client.call("stats")["stats"]
        print(f"Stats: {stats}")
        if stats["done"] == num_tasks:
            break
        time.sleep(0.5)
        
    stop_event.set()
    for t in threads:
        t.join(timeout=1)
        
    final_stats = client.call("stats")["stats"]
    print(f"Final Stats: {final_stats}")
    
    assert final_stats["done"] == num_tasks
    assert final_stats["queued"] == 0
    assert final_stats["leased"] == 0
    
    # Verify worker distribution
    # We need to check the DB or list tasks to see who did what
    tasks = client.call("list", {"limit": num_tasks, "status": "done"})["tasks"]
    worker_ids = set(t["worker_id"] for t in tasks if t["worker_id"])
    
    print(f"Unique workers that processed tasks: {len(worker_ids)}")
    # Ideally, multiple workers should have picked up tasks. 
    # With 20 tasks and 5 workers, it's highly likely > 1 worker was used.
    assert len(worker_ids) > 1
