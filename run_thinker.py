from __future__ import annotations
import time
import uuid
import json
import socket
from typing import Any

# --- Client Logic (Duplicated from agent.py for standalone usage) ---
class HubClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req_id = str(uuid.uuid4())
        req = {"id": req_id, "method": method, "params": params or {}}
        
        with socket.create_connection((self.host, self.port)) as sock:
            sock.sendall((json.dumps(req) + "\n").encode("utf-8"))
            f = sock.makefile("r")
            line = f.readline()
            if not line:
                raise RuntimeError("Empty response from hub")
            resp = json.loads(line)
            
        if resp.get("error"):
            raise RuntimeError(f"Hub error: {resp['error']}")
        return resp["result"]

# --- Thinker Loop Logic ---

def run_thinker_loop(hub_host: str = "localhost", hub_port: int = 8766):
    client = HubClient(hub_host, hub_port)
    
    goal = "What are the top 3 risks of using AI in the public sector, and how can they be mitigated?"
    
    print(f"--- Starting Thinker Loop ---")
    print(f"Goal: {goal}\n")

    # 1. Generator Step
    print("1. [Generator] Generating initial thoughts...")
    generator_system_prompt = (
        "You are a creative and exhaustive researcher. "
        "Generate a comprehensive list of potential risks and mitigations. "
        "Be bold and cover all angles."
    )
    gen_task_id = client.call("enqueue", {
        "prompt": goal,
        "system_prompt": generator_system_prompt
    })["task_id"]
    
    gen_result = wait_for_result(client, gen_task_id)
    print(f"\n[Generator Output]:\n{gen_result}\n")

    # 2. Judge Step
    print("2. [Judge] Critically evaluating the output...")
    judge_system_prompt = (
        "You are a strict, axiomatic judge. "
        "Evaluate the provided text for accuracy, feasibility, and completeness. "
        "Identify any weak points or vague statements. "
        "If the output is good, summarize the top 3 points clearly. "
        "If it's lacking, explain why."
    )
    judge_prompt = f"Original Goal: {goal}\n\nProposed Answer:\n{gen_result}"
    
    judge_task_id = client.call("enqueue", {
        "prompt": judge_prompt,
        "system_prompt": judge_system_prompt
    })["task_id"]
    
    judge_result = wait_for_result(client, judge_task_id)
    print(f"\n[Judge Output]:\n{judge_result}\n")
    
    print("--- Thinker Loop Complete ---")

def wait_for_result(client: HubClient, task_id: int, poll_interval: float = 1.0) -> str:
    print(f"Waiting for task {task_id}...", end="", flush=True)
    while True:
        # In a real app, we'd have a specific 'get_task' method, but 'list' works for now
        # We filter by checking the list. This is inefficient for large DBs but fine for this demo.
        # Actually, let's just poll list with a limit and check if our ID is there and done.
        # A better way in the future would be `get_task(id)`.
        
        # For now, we just wait a bit and assume the agent picks it up.
        # To be robust, we should implement `get_task` in Hub, but let's stick to existing methods.
        # We can use `list` and filter client-side or just wait.
        
        # Let's implement a simple poller using `list`
        tasks = client.call("list", {"limit": 100})["tasks"]
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if task:
            if task["status"] == "done":
                print(" Done!")
                return task["result"]
            elif task["status"] == "failed":
                print(" Failed!")
                raise RuntimeError(f"Task {task_id} failed: {task.get('error')}")
        
        print(".", end="", flush=True)
        time.sleep(poll_interval)

if __name__ == "__main__":
    run_thinker_loop()
