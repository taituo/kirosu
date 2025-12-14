import pytest
import time
import threading
from kiro_swarm.agent import KiroAgent, HubClient

def test_system_flow(hub_port):
    client = HubClient("127.0.0.1", hub_port)
    
    # Enqueue a task
    resp = client.call("enqueue", {"prompt": "kiro-cli --version"})
    task_id = resp["task_id"]
    assert task_id > 0
    
    # Start an agent in a thread
    agent = KiroAgent("127.0.0.1", hub_port)
    stop_event = threading.Event()
    
    def agent_loop():
        while not stop_event.is_set():
            agent._tick()
            time.sleep(0.1)
            
    t = threading.Thread(target=agent_loop, daemon=True)
    t.start()
    
    # Wait for task to be done
    start = time.time()
    result = None
    while time.time() - start < 10:
        tasks = client.call("list", {"limit": 10, "status": "done"})["tasks"]
        done_task = next((t for t in tasks if t["task_id"] == task_id), None)
        if done_task:
            result = done_task["result"]
            break
        time.sleep(0.5)
        
    stop_event.set()
    t.join(timeout=1)
    
    assert result is not None
    assert "kiro-cli" in result or "version" in result
