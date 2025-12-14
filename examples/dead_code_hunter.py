import os
import time
from kirosu.agent import HubClient

def main():
    HOST = "127.0.0.1"
    PORT = int(os.environ.get("KIRO_SWARM_PORT", 8765))
    client = HubClient(HOST, PORT)
    
    print("1. Enqueuing Dead Code Analysis Task...")
    # In a real scenario, this would be a complex script or tool invocation
    analysis_prompt = """
    Analyze the following Python code and identify unused functions:
    
    ```python
    def used_function():
        print("I am used")
        
    def unused_function():
        print("I am lonely")
        
    def main():
        used_function()
        
    if __name__ == "__main__":
        main()
    ```
    
    Return a JSON list of unused function names.
    """
    
    resp = client.call("enqueue", {"prompt": analysis_prompt, "type": "chat"})
    analysis_task_id = resp["task_id"]
    print(f"Analysis Task ID: {analysis_task_id}")
    
    # Wait for analysis
    unused_functions = []
    while True:
        tasks = client.call("list", {"limit": 100})["tasks"]
        task = next((t for t in tasks if t["task_id"] == analysis_task_id), None)
        if task and task["status"] == "done":
            print(f"Analysis Result: {task['result']}")
            # Mock parsing logic
            if "unused_function" in task["result"]:
                unused_functions = ["unused_function"]
            break
        time.sleep(1)
        
    if not unused_functions:
        print("No dead code found.")
        return

    print(f"\n2. Enqueuing Pruning Task for: {unused_functions}")
    # Dangerous task to remove the code
    prune_prompt = f"""
    Write a Python script to remove the function definition for '{unused_functions[0]}' from the file 'target.py'.
    Assume 'target.py' contains the code analyzed above.
    Output ONLY the python code.
    """
    
    resp = client.call("enqueue", {"prompt": prune_prompt, "type": "chat"})
    prune_task_id = resp["task_id"]
    print(f"Pruning Generation Task ID: {prune_task_id}")
    
    # Wait for script generation
    prune_script = ""
    while True:
        tasks = client.call("list", {"limit": 100})["tasks"]
        task = next((t for t in tasks if t["task_id"] == prune_task_id), None)
        if task and task["status"] == "done":
            prune_script = task["result"]
            break
        time.sleep(1)
        
    print(f"Generated Pruning Script:\n{prune_script}")
    
    # Execute pruning (Dangerous)
    # resp = client.call("enqueue", {"prompt": prune_script, "type": "python"})
    # print(f"Pruning Execution Task ID: {resp['task_id']}")

if __name__ == "__main__":
    main()
