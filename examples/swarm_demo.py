import os
import time
import subprocess
import sys
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = int(os.environ.get("KIRO_SWARM_PORT", 9000)) # Use 9000 to match previous demo
    client = HubClient(HOST, PORT)
    
    # Ensure demo_artifacts directory exists
    os.makedirs("demo_artifacts/swarm", exist_ok=True)
    
    print(f"1. Spawning 10 Agents (connecting to {HOST}:{PORT})...")
    agents = []
    env = os.environ.copy()
    env["KIRO_SWARM_PORT"] = str(PORT)
    
    for i in range(10):
        # We use the same python interpreter
        cmd = [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(PORT)]
        p = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        agents.append(p)
        
    print("Agents spawned. Waiting 2s for them to connect...")
    time.sleep(2)
    
    print("2. Enqueuing 10 Tasks...")
    task_ids = []
    for i in range(10):
        filename = f"demo_artifacts/swarm/worker_{i}.txt"
        prompt = f"""
        Write a file named '{filename}' with the content:
        "Worker {i} was here at {time.time()}"
        Use python to write the file.
        """
        resp = client.call("enqueue", {"prompt": prompt, "type": "chat"})
        task_ids.append(resp["task_id"])
        
    print(f"Enqueued {len(task_ids)} tasks.")
    
    # Wait for completion
    print("3. Waiting for completion...")
    start_time = time.time()
    while True:
        resp = client.call("list", {"limit": 100, "status": "done"})
        done_count = len(resp["tasks"])
        # We also check failed just in case
        resp_failed = client.call("list", {"limit": 100, "status": "failed"})
        failed_count = len(resp_failed["tasks"])
        
        # Filter for our specific tasks if needed, but for demo we assume clean DB or just count
        # Better: check if our task_ids are in the done/failed lists
        done_ids = {t["task_id"] for t in resp["tasks"]}
        failed_ids = {t["task_id"] for t in resp_failed["tasks"]}
        
        completed = 0
        for tid in task_ids:
            if tid in done_ids or tid in failed_ids:
                completed += 1
                
        print(f"Progress: {completed}/{len(task_ids)} (Done: {len(done_ids)}, Failed: {len(failed_ids)})", end="\r")
        
        if completed == len(task_ids):
            print("\nAll tasks completed!")
            break
            
        if time.time() - start_time > 60:
            print("\nTimeout waiting for tasks!")
            break
            
        time.sleep(1)
        
    # Verify artifacts
    print("4. Verifying artifacts...")
    found = 0
    for i in range(10):
        filename = f"demo_artifacts/swarm/worker_{i}.txt"
        if os.path.exists(filename):
            found += 1
        else:
            print(f"Missing: {filename}")
            
    print(f"Found {found}/10 artifacts.")
    
    # Cleanup
    print("5. Terminating agents...")
    for p in agents:
        p.terminate()
        
    if found == 10:
        print("✅ Swarm Demo Successful!")
    else:
        print("❌ Swarm Demo Failed!")

if __name__ == "__main__":
    main()
