import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
import random
from kirosu.client import SwarmClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("LiveMonitor")

HUB_PORT = 8780  # Distinct port
DB_PATH = "live_monitor.db"

# --- THE INTERNAL TOOL CODE ---
# This code is what the "Monitor Agent" will execute.
# It simulates a high-frequency websocket connection.
MONITOR_TOOL_CODE = """
import time
import random
import asyncio
import os
from kirosu.client import SwarmClient

async def monitor_loop():
    print(">> [INTERNAL TOOL] Connecting to 'Simulated Crypto/Sports Stream'...")
    
    # Connect to Hub so we can signal an opportunity
    # (In a real app, this might be passed in env vars)
    async with SwarmClient(port=8780) as client:
        
        # Simulate high-frequency polling (e.g. 100ms)
        price = 100.0
        
        for i in range(50): # Run for max 5 seconds for simulation
            time.sleep(0.1) 
            
            # Random walk
            change = random.uniform(-2.0, 2.0)
            price += change
            
            # FORCE CRASH FOR DEMO
            if i > 10:
                price = 90.0 # Crash it!

            # Visual feedback of high-speed stream
            print(f">> [STREAM] BTC/USD: {price:.2f}")
            
            # THRESHOLD TRIGGER: Price drops below 95 (Buy Opportunity)
            if price < 95.0:
                print(f">> [TRIGGER] Price {price:.2f} < 95.0! SIGNALING BUY!")
                
                # Fast Handoff: Enqueue task for the 'Trader' agent
                task_id = await client.add_task(
                    prompt=f"EXECUTE BUY ORDER: BTC @ {price:.2f}", 
                    task_type="chat"
                )
                print(f">> [INTERNAL TOOL] Signal sent! Task ID: {task_id}")
                return f"OPPORTUNITY DETECTED at {price:.2f}. Handoff to Task {task_id}"
                
        return "No opportunity found in session."

if __name__ == "__main__":
    asyncio.run(monitor_loop())
"""

def start_process(cmd, name):
    logger.info(f"🚀 Starting {name}...")
    proc = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        env=os.environ.copy()
    )
    return proc

async def run_demo():
    # 1. Cleanup
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            time.sleep(1)
        except OSError:
            pass

    # 2. Start Hub
    hub_process = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH],
        "Hub"
    )
    time.sleep(2)

    # 3. Start Agents
    # Agent 1: The Monitor (Runs Python code, specialized execution)
    # Agent 2: The Trader (Runs LLM Chat, makes decisions)
    agents = []
    
    # We force 'Monitor' to use standard python local execution tools if we had them,
    # but here we just use the same agent binary.
    # Note: Monitor needs to be able to run python code.
    
    provider = os.getenv("KIRO_PROVIDER", "kiro")
    model = os.getenv("MITTELO_KIRO_MODEL", "claude-haiku-4.5")
    
    # Monitor Agent (ID: monitor_bot)
    agents.append(start_process([
        sys.executable, "-m", "kirosu.cli", "agent",
        "--port", str(HUB_PORT),
        "--id", "monitor_bot",
        "--model", model
    ], "Monitor Bot"))

    # Trader Agent (ID: trader_bot)
    agents.append(start_process([
        sys.executable, "-m", "kirosu.cli", "agent",
        "--port", str(HUB_PORT),
        "--id", "trader_bot",
        "--model", model
    ], "Trader Bot"))
    
    time.sleep(2)

    async with SwarmClient(port=HUB_PORT) as client:
        # Step 1: Instruct Monitor Bot to start the loop
        logger.info("\n--- 📡 PHASE 1: STARTING MONITOR ---")
        logger.info("Injecting the 'Internal Loop' python script...")
        
        # We manually enqueue a PYTHON task for the Monitor
        # This simulates the Monitor Agent deciding to run a tool, or being tasked to run a script.
        # In this demo, we bypass the LLM "writing" the script and just inject it for speed.
        
        # Note: We must ensure we target the monitor_bot or just rely on first available.
        # Since we don't have task-affinity yet in Hub (lease filtering), 
        # we assume probabilistic assignment or just that any agent can do it.
        # Ideally, we'd have `target_worker_id` in enqueue. 
        # For now, we utilize the fact that Kiro supports Python tasks.
        
        monitor_task_id = await client._send_request("enqueue", {
            "prompt": MONITOR_TOOL_CODE,
            "type": "python", # EXECUTE THIS CODE
            "context": {}
        })
        logger.info(f"Monitor Task {monitor_task_id['task_id']} enqueued.")

        # Step 2: Watch for results
        # We expect the Monitor to eventually trigger and enqueue a NEW task for the Trader.
        logger.info("Waiting for signals...")
        
        start_time = time.time()
        tasks_seen = set()
        tasks_seen.add(monitor_task_id['task_id'])
        
        while time.time() - start_time < 30:
            # Poll for new tasks
            resp = await client._send_request("list", {"limit": 10})
            tasks = resp.get("tasks", [])
            
            for t in tasks:
                tid = t['task_id']
                if tid not in tasks_seen:
                    logger.info(f"\n🚨 NEW TASK DETECTED: ID {tid}")
                    logger.info(f"Prompt: {t['prompt']}")
                    logger.info("This task was spawned by the Monitor Agent's internal loop!")
                    tasks_seen.add(tid)
                    
                if t['status'] == 'done' and t['result']:
                     if "OPPORTUNITY" in t['result']:
                         logger.info(f"✅ Monitor reported: {t['result']}")
                         
            await asyncio.sleep(1)

    # Cleanup
    hub_process.terminate()
    for p in agents:
        p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        pass
