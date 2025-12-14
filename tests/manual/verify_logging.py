import os
import time
import subprocess
import sys
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = 9100
    DB_PATH = "logging_test.db"
    LOG_FILE = "test_agent.log"
    
    # Clean up previous run
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        
    print("1. Starting Hub...")
    hub_cmd = [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(PORT), "--db", DB_PATH]
    hub_proc = subprocess.Popen(hub_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    print(f"2. Starting Agent with --log-file {LOG_FILE} --verbose...")
    env = os.environ.copy()
    env["KIRO_SWARM_PORT"] = str(PORT)
    agent_cmd = [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(PORT), "--log-file", LOG_FILE, "--verbose"]
    agent_proc = subprocess.Popen(agent_cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    print("3. Enqueuing Task...")
    client = HubClient(HOST, PORT)
    try:
        resp = client.call("enqueue", {"prompt": "echo 'logging test'", "type": "chat"})
        task_id = resp["task_id"]
        print(f"Task ID: {task_id}")
        
        # Wait for completion
        print("4. Waiting for completion...")
        for _ in range(10):
            tasks = client.call("list", {"limit": 10, "status": "done"})["tasks"]
            if any(t["task_id"] == task_id for t in tasks):
                print("Task done.")
                break
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("5. Terminating processes...")
        agent_proc.terminate()
        hub_proc.terminate()
        agent_proc.wait()
        hub_proc.wait()
        
    print("6. Verifying Log File...")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            content = f.read()
            print(f"Log File Size: {len(content)} bytes")
            if "Agent" in content and "started" in content:
                print("✅ Log file contains expected content.")
                print("--- Log Preview ---")
                print(content[:200] + "...")
            else:
                print("❌ Log file content missing expected strings.")
                print(content)
    else:
        print("❌ Log file not found.")

if __name__ == "__main__":
    main()
