import os
import time
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = int(os.environ.get("KIRO_SWARM_PORT", 8765))
    client = HubClient(HOST, PORT)
    
    # Scenario: We found a potential bug in a file
    buggy_code = """
def add(a, b):
    return a - b  # Bug: subtraction instead of addition
"""
    
    print("1. Enqueuing Bug Reproduction Task...")
    # We ask the agent to write a reproduction script
    repro_prompt = f"""
    Here is a function that is supposed to add two numbers, but it seems buggy:
    {buggy_code}
    
    Write a Python script that asserts 2 + 2 == 4 using this function, and fails if it's wrong.
    Output ONLY the python code.
    """
    
    resp = client.call("enqueue", {"prompt": repro_prompt, "type": "chat"})
    repro_task_id = resp["task_id"]
    print(f"Reproduction Task ID: {repro_task_id}")
    
    # Wait for reproduction script
    while True:
        tasks = client.call("list", {"limit": 100})["tasks"]
        task = next((t for t in tasks if t["task_id"] == repro_task_id), None)
        if task and task["status"] == "done":
            repro_script = task["result"]
            break
        time.sleep(1)
        
    print(f"Generated Reproduction Script:\n{repro_script}")
    
    print("\n2. Enqueuing Verification Task (Dangerous)...")
    # Now we run the script using the "python" task type
    resp = client.call("enqueue", {"prompt": repro_script, "type": "python"})
    verify_task_id = resp["task_id"]
    print(f"Verification Task ID: {verify_task_id}")
    
    # Wait for verification
    while True:
        tasks = client.call("list", {"limit": 100})["tasks"]
        task = next((t for t in tasks if t["task_id"] == verify_task_id), None)
        if task and task["status"] in ["done", "failed"]:
            print(f"Verification Result: {task['status']}")
            print(f"Output: {task.get('result') or task.get('error')}")
            break
        time.sleep(1)

if __name__ == "__main__":
    main()
