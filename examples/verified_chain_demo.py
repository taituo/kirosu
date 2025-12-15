import asyncio
import logging
import os
import signal
import subprocess
import sys
import time
from kirosu.client import SwarmClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VerifiedChain")

HUB_PORT = 8770  # Use a distinct port to avoid conflicts
DB_PATH = "verified_chain.db"

def start_process(cmd, name):
    """Helper to start background processes"""
    logger.info(f"🚀 Starting {name}...")
    proc = subprocess.Popen(
        cmd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        env=os.environ.copy()
    )
    return proc

async def run_chain():
    # 1. Cleanup old DB
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
    time.sleep(2)  # Wait for Hub

    # 3. Start Agents (4 Workers: Maker1, Checker1, Maker2, Checker2)
    # We use the same 'model' for all, but distinct IDs implies distinct roles/context if we were using isolated workdirs.
    agents = []
    agent_ids = ["maker_v1", "checker_v1", "maker_v2", "checker_v2"]
    
    # Check if we are using Codex or Standard
    provider = os.getenv("KIRO_PROVIDER", "kiro")
    model = os.getenv("MITTELO_KIRO_MODEL", "claude-haiku-4.5")
    logger.info(f"🤖 Spawning agents using Provider: {provider}, Model: {model}")

    for aid in agent_ids:
        cmd = [
            sys.executable, "-m", "kirosu.cli", "agent",
            "--host", "localhost",
            "--port", str(HUB_PORT),
            "--id", aid,
            "--model", model
        ]
        # Provider handles flags internally
            
        p = start_process(cmd, f"Agent {aid}")
        agents.append(p)
    
    time.sleep(3) # Let agents connect

    async with SwarmClient(host="localhost", port=HUB_PORT) as client:
        
        # --- STAGE 1: GENERATION ---
        
        logger.info("\n--- 📝 STAGE 1: MAKER (Python Function) ---")
        task1_prompt = "Write a Python function called 'fibonacci' that calculates the nth sequence number. output ONLY the code."
        task1_id = await client.add_task(task1_prompt)
        logger.info(f"Task 1 submitted: {task1_id}")
        
        # Wait for result
        result1 = ""
        while True:
            t = await client.get_task(task1_id)
            if t['status'] == 'done':
                result1 = t['result']
                logger.info(f"✅ Maker 1 Finished:\n{result1}")
                break
            await asyncio.sleep(1)

        # --- STAGE 2: VERIFICATION ---
        
        logger.info("\n--- 🕵️ STAGE 2: CHECKER (Verify Python) ---")
        task2_prompt = f"Review this code. If it is valid Python, reply 'APPROVED'. If not, reply 'REJECTED'. Code:\n{result1}"
        task2_id = await client.add_task(task2_prompt)
        
        valid_v1 = False
        while True:
            t = await client.get_task(task2_id)
            if t['status'] == 'done':
                verdict = t['result'].strip()
                logger.info(f"✅ Checker 1 Verdict: {verdict}")
                if "APPROVED" in verdict.upper():
                    valid_v1 = True
                break
            await asyncio.sleep(1)

        if not valid_v1:
            logger.error("🛑 Chain halted: Stage 1 verification failed.")
            return

        # --- STAGE 3: TRANSFORMATION (Python -> JavaScript) ---
        
        logger.info("\n--- 🔄 STAGE 3: MAKER 2 (Translate to JS) ---")
        task3_prompt = f"Translate this Python function to JavaScript. Output ONLY the code.\n{result1}"
        task3_id = await client.add_task(task3_prompt)
        
        result2 = ""
        while True:
            t = await client.get_task(task3_id)
            if t['status'] == 'done':
                result2 = t['result']
                logger.info(f"✅ Maker 2 Finished:\n{result2}")
                break
            await asyncio.sleep(1)

        # --- STAGE 4: FINAL VERIFICATION ---
        
        logger.info("\n--- 🕵️ STAGE 4: CHECKER 2 (Verify JS) ---")
        task4_prompt = f"Review this JS code. If it is valid, reply 'APPROVED'. Code:\n{result2}"
        task4_id = await client.add_task(task4_prompt)
        
        while True:
            t = await client.get_task(task4_id)
            if t['status'] == 'done':
                verdict = t['result'].strip()
                logger.info(f"✅ Checker 2 Verdict: {verdict}")
                break
            await asyncio.sleep(1)

    logger.info("\n🏁 Verified Chain Demo Complete!")

    # Cleanup
    hub_process.terminate()
    for p in agents:
        p.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(run_chain())
    except KeyboardInterrupt:
        pass
