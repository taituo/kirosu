import pytest
import os
import tempfile
import threading
import time
from kiro_swarm.db import TaskStore
from kiro_swarm.hub import run_hub
from kiro_swarm.agent import KiroAgent

@pytest.fixture
def db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def store(db_path):
    s = TaskStore(db_path)
    yield s
    s.close()

@pytest.fixture
def hub_port(db_path):
    # Start hub on random port (0)
    # run_hub returns the actual port
    port_container = {"port": None}
    
    def target():
        def cb(port):
            port_container["port"] = port
            
        run_hub(db_path, "127.0.0.1", 0, 300, ready_callback=cb)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    
    # Wait for port to be assigned
    start = time.time()
    while port_container["port"] is None:
        if time.time() - start > 5:
            raise RuntimeError("Hub failed to start")
        time.sleep(0.01)
        
    return port_container["port"]
