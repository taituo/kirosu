import os
import time
import subprocess
import sys
import shutil
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = 9200
    DB_PATH = "context_test.db"
    LOG_FILE = "context_agent.log"
    CONTEXT_DIR = ".kiro"
    CONTEXT_FILE = os.path.join(CONTEXT_DIR, "context.md")
    
    # Clean up
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    if os.path.exists(CONTEXT_DIR):
        shutil.rmtree(CONTEXT_DIR)
        
    # Create Context
    os.makedirs(CONTEXT_DIR)
    with open(CONTEXT_FILE, "w") as f:
        f.write("You are a helpful assistant named KiroBot.")
        
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
        resp = client.call("enqueue", {"prompt": "What is your name?", "type": "chat"})
        task_id = resp["task_id"]
        print(f"Task ID: {task_id}")
        
        # Wait for completion
        print("4. Waiting for completion...")
        for _ in range(15):
            tasks = client.call("list", {"limit": 10, "status": "done"})["tasks"]
            task = next((t for t in tasks if t["task_id"] == task_id), None)
            if task:
                print(f"Task done. Result: {task['result']}")
                if "KiroBot" in task['result']:
                    print("✅ Agent knew its name (Context Injected)!")
                else:
                    print("❌ Agent did NOT know its name.")
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
        
    print("6. Verifying Log File for Injection Message...")
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            content = f.read()
            if "Injected context from" in content:
                print("✅ Log confirms context injection.")
            else:
                print("❌ Log missing injection confirmation.")

if __name__ == "__main__":
    main()
