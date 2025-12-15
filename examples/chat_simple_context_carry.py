import asyncio
import logging
import os
import sys
import subprocess
import time
from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.ERROR)
logging.getLogger("SwarmClient").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

HUB_PORT = 8791
MEMORY_FILE = "context_memory.md"

# ---------------- HELPERS ----------------

def start_process(cmd, name):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy()
    )

async def run_agent_task(client, agent_id, system_prompt, user_prompt):
    """Generic function to run a single turn with an agent."""
    full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
    task_id = await client.add_task(full_prompt, task_type="chat")
    
    print(f"⏳ Waiting for {agent_id}...")
    while True:
        await asyncio.sleep(0.5)
        status = await client._send_request("list", {"limit": 5}) 
        for t in status.get('tasks', []):
            if t['task_id'] == task_id and t['status'] == 'done':
                return t['result']

# ---------------- MAIN ----------------

async def main():
    # 1. CLEANUP
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
    
    # 2. START INFRA
    print("🚀 Starting Hub...")
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT)], "Hub"
    )
    time.sleep(2)

    async with SwarmClient(port=HUB_PORT) as client:
        
        # --- PHASE 1: THE WRITER (Agent A) ---
        print("\n" + "="*50)
        print("📝 PHASE 1: THE WRITER (Agent A)")
        print("="*50)
        
        # Start Agent A
        agent_a = start_process(
            [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "WRITER", "--model", "gpt-5.1-codex-mini"], 
            "Writer"
        )
        time.sleep(2)
        
        print("\n🤖 (Agent A is listening)")
        topic = input("👉 What should the Writer create? (e.g. 'Short story about a cat'): ").strip()
        if not topic: topic = "Haiku about code"
        
        story = await run_agent_task(client, "WRITER", 
            "You are a creative writer. Keep it short.",
            topic
        )
        print(f"\n[WRITER OUTPUT]:\n{story}\n")
        
        # SIMULATE /context save
        print(f"💾 Saving Context to '{MEMORY_FILE}'...")
        with open(MEMORY_FILE, "w") as f:
            f.write(f"# MEMORY DUMP\nContext: {topic}\n\n## Stick Note from Agent A\n{story}")
            
        # Kill Agent A (Simulate session end)
        agent_a.terminate()
        print("💀 Agent A has ended process.")
        
        # --- PHASE 2: THE EDITOR (Agent B) ---
        print("\n" + "="*50)
        print("🧐 PHASE 2: THE EDITOR (Agent B)")
        print("="*50)
        print("   (Loading previous memory...)")
        time.sleep(1)

        # Start Agent B
        agent_b = start_process(
            [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "EDITOR", "--model", "gpt-5.1-codex-mini"], 
            "Editor"
        )
        time.sleep(2)
        
        # SIMULATE /context load
        print(f"📂 Loading Context from '{MEMORY_FILE}'...")
        with open(MEMORY_FILE, "r") as f:
            memory_content = f.read()
        
        print("\n🤖 (Agent B has read the file)")
        instr = input("👉 What should Agent B do with this text? (e.g. 'Critique it', 'Translate to Finnish'): ").strip()
        if not instr: instr = "Summarize it"
            
        critique = await run_agent_task(client, "EDITOR",
            f"""You are an helpful Agent.
You have been given a MEMORY DUMP from a previous session.
<memory_dump>
{memory_content}
</memory_dump>
Use this memory to answer the user's question.
""",
            instr
        )
        print(f"\n[EDITOR OUTPUT]:\n{critique}\n")

    # CLEANUP
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
    print("✅ Demo Complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user.")
    finally:
        # Global Cleanup (Runs on Success AND Ctrl+C)
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
        if os.path.exists(MEMORY_FILE): 
            os.remove(MEMORY_FILE)
            print(f"🗑️  Deleted temporary context file: '{MEMORY_FILE}'")
