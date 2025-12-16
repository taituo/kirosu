#!/usr/bin/env python3
"""
Context Sieve Demo: Handling Massive Data with Sub-Agents
---------------------------------------------------------
Problem: A "Fetch Logs" tool might return 10MB of text, crashing the context window.
Solution: Delegate this to a "Sieve Agent" that consumes the noise and returns only the Summary.

Scenario:
1. Main Agent wants to know error rates.
2. Main Agent tasks Sieve Agent.
3. Sieve Agent calls `fetch_massive_logs()` (simulated 10MB).
4. Sieve Agent analyzes it internally.
5. Sieve Agent returns concise answer to Main Agent.
6. Main Agent never sees the 10MB blob.
"""

import os
import sys
import time
import threading
import logging
import random
import uuid
from typing import Any

# Project setup
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kirosu.hub import run_hub
from kirosu.agent import HubClient

# --- Simulated "Noisy" MCP Tool ---

def fetch_massive_logs(date: str) -> str:
    """
    Fetches server logs. WARNING: Returns extremely large output (simulated 5000 lines).
    """
    print(f"\n[Tool] Generating massive logs for {date}...")
    
    # Generate 5,000 lines of noise
    lines = []
    errors = 0
    for i in range(5000):
        timestamp = f"2023-10-27T{i%24:02}:{i%60:02}:{i%60:02}"
        if random.random() < 0.02: # 2% error rate
            lines.append(f"{timestamp} ERROR Connection timed out to DB-shard-{i%10}")
            errors += 1
        else:
            lines.append(f"{timestamp} INFO Request served 200 OK latency={random.randint(10, 500)}ms")
            
    # Add a needle in the haystack
    lines.append(f"2023-10-27T23:59:59 CRITICAL SYSTEM MELTDOWN DETECTED: REACTOR CORE 4")
    
    output = "\n".join(lines)
    print(f"[Tool] Returning {len(output)} chars of log data (approx {len(output)/1024:.1f} KB).")
    return output

# --- Specialized Sieve Worker ---

class SieveWorker:
    def __init__(self, host: str, port: int, name: str):
        self.client = HubClient(host, port)
        self.worker_id = f"sieve-{uuid.uuid4().hex[:8]}"
        self.name = name
    
    def run_loop(self):
        print(f"[{self.name}] Started (Specialized Data Filter).")
        while True:
            try:
                # 1. Lease task
                resp = self.client.call("lease", {"worker_id": self.worker_id, "max_tasks": 1, "lease_seconds": 60})
                tasks = resp.get("tasks", [])
                
                if not tasks:
                    time.sleep(1)
                    continue
                    
                task = tasks[0]
                task_id = task["task_id"]
                prompt = task["prompt"]
                
                # 2. Check if we can handle it (Routing)
                if "logs" in prompt.lower():
                    print(f"[{self.name}] Intercepted task: {prompt[:40]}...")
                    self._handle_massive_data(task_id, prompt)
                else:
                    # Not for us? In real world, maybe release it. Here we just fail it.
                    print(f"[{self.name}] Unknown task type: {prompt}")
                    self.client.call("ack", {"task_id": task_id, "status": "failed", "error": "Unknown task"})
                    
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
                time.sleep(1)

    def _handle_massive_data(self, task_id: int, prompt: str):
        # 3. CALL THE NOISY TOOL (Simulated MCP call)
        # This is where the massive data ingestion happens context-free
        raw_data = fetch_massive_logs("2023-10-27")
        
        # 4. FILTER / ANALYZE (The "Sieve")
        # In a real agent, this might be a python script or a streamed LLM call.
        # Here we do simple string processing to simulate "Machine Intelligence" 
        # extracting the signal from noise.
        print(f"[{self.name}] Analyzing {len(raw_data)} bytes of raw data...")
        
        error_count = raw_data.count("ERROR")
        critical_alert = "None"
        for line in raw_data.splitlines():
            if "CRITICAL" in line:
                critical_alert = line
        
        # 5. SUMMARIZE
        summary = (
            f"Log Analysis Report:\n"
            f"- Total Lines Processed: {len(raw_data.splitlines())}\n"
            f"- Error Count: {error_count}\n"
            f"- Critical Alerts: {critical_alert}"
        )
        
        print(f"[{self.name}] Reduced data size: {len(raw_data)} chars -> {len(summary)} chars.")
        
        # 6. RETURN SUMMARY ONLY
        self.client.call("ack", {"task_id": task_id, "status": "done", "result": summary})


def run_demo():
    PORT = 9500
    DB_PATH = "demo_sieve.db"
    
    # 1. Start Hub
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    t = threading.Thread(target=run_hub, args=(DB_PATH, "127.0.0.1", PORT, 300), daemon=True)
    t.start()
    time.sleep(2)
    
    # 2. Start Sieve Agent (Specialized)
    sieve = SieveWorker("127.0.0.1", PORT, "LogAnalyzer")
    t_sieve = threading.Thread(target=sieve.run_loop, daemon=True)
    t_sieve.start()
    
    # 3. Simulate Main Agent requesting help
    # In a real swarm, the Main Agent would perform this 'call'
    client = HubClient("127.0.0.1", PORT)
    
    print("\n[Manager] Enqueuing task for LogAnalyzer...")
    client.call("enqueue", {
        "prompt": "Check logs for 2023-10-27", 
        "task_type": "chat"  # SieveWorker will pick this up
    })
    
    # 4. Monitor
    print("Watching for result...\n")
    start_time = time.time()
    while time.time() - start_time < 30:
        status = client.call("list", {"limit": 10})
        tasks = status.get("tasks", [])
        if tasks:
            t = tasks[0]
            if t["status"] == "done":
                print(f"\n🏆 FINAL RESULT (in Main Context):\n{t['result']}")
                break
        time.sleep(1)

    # Cleanup
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    if os.path.exists(DB_PATH + "-wal"): os.remove(DB_PATH + "-wal")
    if os.path.exists(DB_PATH + "-shm"): os.remove(DB_PATH + "-shm")

if __name__ == "__main__":
    run_demo()
