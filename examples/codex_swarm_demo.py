import threading
import time
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kirosu.hub import run_hub
from kirosu.agent import KiroAgent, HubClient
from kirosu.db import TaskStore

# Setup Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")

def worker_thread(idx):
    # Set Provider to Codex
    os.environ["KIRO_PROVIDER"] = "codex"
    # Ensure verbose logging is passed to agent
    agent = KiroAgent("127.0.0.1", 8800, model="gpt-5.1-codex-mini", agent_name=f"worker-{idx}")
    
    logging.info(f"Worker {idx} started (Provider: Codex) - REAL EXECUTION")
    
    # Run loop (attempt 5 ticks)
    # We catch errors here so one worker failure doesn't kill the demo, 
    # but we log them clearly.
    for i in range(5):
        try:
            agent._tick()
            time.sleep(0.5)
        except Exception as e:
            logging.error(f"Worker {idx} error: {e}")
            break

def main():
    # 1. Start Hub
    db_path = "demo_swarm.db"
    if os.path.exists(db_path): os.remove(db_path)
    
    hub_thread = threading.Thread(target=run_hub, args=(db_path, "127.0.0.1", 8800, 300))
    hub_thread.daemon = True
    hub_thread.start()
    time.sleep(2) # Warmup

    # 2. Enqueue 5 Tasks (Real Codex might be slow/expensive, so let's do 5)
    logging.info("--- Enqueuing 5 Tasks ---")
    client = HubClient("127.0.0.1", 8800)
    for i in range(5):
        client.call("enqueue", {"prompt": f"Explain the number {i} in one sentence."})

    # 3. Start 5 Workers
    logging.info("--- Starting 5 Codex Workers ---")
    workers = []
    for i in range(5):
        t = threading.Thread(target=worker_thread, args=(i,))
        t.start()
        workers.append(t)

    # 4. Wait for completion
    for t in workers:
        t.join()

    # 5. Check Stats
    logging.info("--- Demo Complete. Final Stats: ---")
    try:
        stats = client.call("list", {"limit": 1})["stats"]
        print(stats)
    except Exception as e:
        print(f"Failed to get stats: {e}")
    
    # Cleanup
    if os.path.exists(db_path): os.remove(db_path)
    if os.path.exists(db_path + "-wal"): os.remove(db_path + "-wal")
    if os.path.exists(db_path + "-shm"): os.remove(db_path + "-shm")

if __name__ == "__main__":
    main()
