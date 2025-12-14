import pytest
import os
import threading
import time
from fastapi.testclient import TestClient
from kirosu.api import app
from kirosu.hub import run_hub

client = TestClient(app)

def test_api_flow(db_path):
    # Start hub
    port_container = {"port": None}
    def target():
        def cb(port):
            port_container["port"] = port
        run_hub(db_path, "127.0.0.1", 0, 300, ready_callback=cb)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    
    while port_container["port"] is None:
        time.sleep(0.01)
        
    hub_port = port_container["port"]
    os.environ["KIRO_SWARM_PORT"] = str(hub_port)
    
    # Test Enqueue
    resp = client.post("/tasks", json={"prompt": "api test"})
    assert resp.status_code == 200
    data = resp.json()
    assert "task_id" in data
    task_id = data["task_id"]
    
    # Test List
    resp = client.get("/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) >= 1
    assert data["tasks"][0]["task_id"] == task_id
    
    # Test Stats
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "stats" in data
    
    # Test Auth
    os.environ["KIRO_SWARM_KEY"] = "secret"
    
    # Should fail without token
    resp = client.get("/stats")
    assert resp.status_code == 403
    
    # Should succeed with token
    resp = client.get("/stats", headers={"x-kiro-key": "secret"})
    assert resp.status_code == 200
    
    del os.environ["KIRO_SWARM_KEY"]
