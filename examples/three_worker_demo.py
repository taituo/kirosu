import os
import time
import subprocess
import sys
import shutil
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = 9300
    DB_PATH = "three_worker_demo.db"
    WORKSPACES_ROOT = "workspaces"
    
    # Cleanup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(WORKSPACES_ROOT):
        shutil.rmtree(WORKSPACES_ROOT)
    os.makedirs(WORKSPACES_ROOT)
        
    print("1. Starting Hub...")
    hub_cmd = [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(PORT), "--db", DB_PATH]
    hub_proc = subprocess.Popen(hub_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    agents = []
    print("2. Spawning 3 Agents with isolated workspaces...")
    env = os.environ.copy()
    env["KIRO_SWARM_PORT"] = str(PORT)
    
    for i in range(1, 4):
        worker_name = f"worker_{i}"
        worker_dir = os.path.join(WORKSPACES_ROOT, worker_name)
        os.makedirs(worker_dir)
        
        # Create a context file for each worker to prove they read it
        os.makedirs(os.path.join(worker_dir, ".kiro"), exist_ok=True)
        with open(os.path.join(worker_dir, ".kiro", "context.md"), "w") as f:
            f.write(f"You are {worker_name}. You work in {worker_dir}.")
            
        log_file = os.path.join(worker_dir, "agent.log")
        
        print(f"  - Spawning {worker_name} in {worker_dir} (Log: {log_file})")
        
        # We need to change CWD for the subprocess so it picks up the local .kiro context
        # AND acts on files in that directory by default
        cmd = [
            sys.executable, "-m", "kirosu.cli", "agent",
            "--port", str(PORT),
            "--log-file", "agent.log", # Relative to CWD
            "--verbose"
        ]
        
        p = subprocess.Popen(
            cmd,
            env=env,
            cwd=worker_dir, # CRITICAL: Agent runs inside its workspace
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        agents.append(p)
        
    time.sleep(3) # Wait for connections
    
    print("3. Enqueuing Tasks...")
    client = HubClient(HOST, PORT)
    task_ids = []
    
    # Task 1: Ask for identity (verifies context injection)
    resp = client.call("enqueue", {"prompt": "Who are you and where do you work?", "type": "chat"})
    task_ids.append(resp["task_id"])
    
    # Task 2: Create a file (verifies CWD isolation)
    resp = client.call("enqueue", {"prompt": "Create a file named 'proof.txt' with content 'I was here'. Use python.", "type": "chat"})
    task_ids.append(resp["task_id"])
    
    # Task 3: Another identity check
    resp = client.call("enqueue", {"prompt": "What is your name?", "type": "chat"})
    task_ids.append(resp["task_id"])
    
    print(f"Enqueued {len(task_ids)} tasks. Waiting for completion...")
    
    # Wait loop
    start_time = time.time()
    while True:
        done_tasks = client.call("list", {"limit": 100, "status": "done"})["tasks"]
        if len(done_tasks) >= len(task_ids):
            print("\nAll tasks done!")
            for t in done_tasks:
                print(f"Task {t['task_id']} Result: {t['result'][:100]}...")
            break
            
        if time.time() - start_time > 60:
            print("Timeout!")
            break
        time.sleep(1)
        
    print("4. Verifying Workspaces...")
    for i in range(1, 4):
        worker_name = f"worker_{i}"
        worker_dir = os.path.join(WORKSPACES_ROOT, worker_name)
        proof_file = os.path.join(worker_dir, "proof.txt")
        log_file = os.path.join(worker_dir, "agent.log")
        
        print(f"Checking {worker_name}...")
        if os.path.exists(log_file):
            print(f"  ✅ Log file exists ({os.path.getsize(log_file)} bytes)")
        else:
            print(f"  ❌ Log file missing")
            
        # We don't know WHICH worker picked up the file creation task, so we check if ANY have it
        # But wait, we spawned 3 agents and gave 3 tasks. They might have distributed them.
        # Ideally we'd check if *at least one* proof.txt exists in the system if we didn't target specific workers.
        # But for this demo, we just want to see that *some* work happened in *some* workspace.
        
    # Check if proof.txt exists in ANY workspace
    proofs_found = 0
    for i in range(1, 4):
        p = os.path.join(WORKSPACES_ROOT, f"worker_{i}", "proof.txt")
        if os.path.exists(p):
            print(f"  ✅ Found proof.txt in worker_{i}")
            proofs_found += 1
            
    if proofs_found > 0:
        print("✅ File creation verified.")
    else:
        print("❌ No proof.txt found (Task might have failed or been chat-only).")

    print("5. Terminating...")
    for p in agents:
        p.terminate()
    hub_proc.terminate()
    
    print("Demo Complete.")

if __name__ == "__main__":
    main()
