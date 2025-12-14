import pytest
import time
import threading
import os
from kirosu.agent import KiroAgent, HubClient
from kirosu.hub import run_hub

def test_auth_failure(db_path):
    # Start hub with auth key
    os.environ["KIRO_SWARM_KEY"] = "secret123"
    
    port_container = {"port": None}
    def target():
        def cb(port):
            port_container["port"] = port
        run_hub(db_path, "127.0.0.1", 0, 300, ready_callback=cb)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    
    while port_container["port"] is None:
        time.sleep(0.01)
        
    # Client without key should fail
    os.environ.pop("KIRO_SWARM_KEY", None)
    client = HubClient("127.0.0.1", port_container["port"])
    
    with pytest.raises(RuntimeError) as excinfo:
        client.call("stats")
    assert "Invalid KIRO_SWARM_KEY" in str(excinfo.value)
    
    # Client with wrong key should fail
    client.auth_token = "wrong"
    with pytest.raises(RuntimeError) as excinfo:
        client.call("stats")
    assert "Invalid KIRO_SWARM_KEY" in str(excinfo.value)

    # Client with correct key should succeed
    client.auth_token = "secret123"
    stats = client.call("stats")
    assert "stats" in stats
    
    os.environ.pop("KIRO_SWARM_KEY", None)

def test_dangerous_python(hub_port):
    client = HubClient("127.0.0.1", hub_port)
    
    # Enqueue python task
    code = "print('DANGEROUS EXECUTION SUCCESS')"
    client.call("enqueue", {"prompt": code, "type": "python"})
    
    # Start agent
    agent = KiroAgent("127.0.0.1", hub_port)
    stop_event = threading.Event()
    
    def agent_loop():
        while not stop_event.is_set():
            agent._tick()
            time.sleep(0.1)
            
    t = threading.Thread(target=agent_loop, daemon=True)
    t.start()
    
    # Wait for result
    start = time.time()
    result = None
    while time.time() - start < 5:
        tasks = client.call("list", {"limit": 10, "status": "done"})["tasks"]
        if tasks:
            result = tasks[0]["result"]
            break
        time.sleep(0.1)
        
    stop_event.set()
    t.join(timeout=1)
    
    assert result is not None
    assert "DANGEROUS EXECUTION SUCCESS" in result
