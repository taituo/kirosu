import asyncio
import logging
import os
import sys
import subprocess
import time
from kirosu.client import SwarmClient

# Configure logging to suppress INFO noise
logging.basicConfig(level=logging.ERROR)
logging.getLogger("SwarmClient").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

HUB_PORT = 8790
DB_PATH = "bar_demo.db"

def start_process(cmd, name):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy()
    )

async def run_agent_task(hub_port, agent_id, system_prompt, user_input):
    """Helper to run a single task on a specific agent (conceptually)."""
    full_prompt = f"System: {system_prompt}\n\nUser: {user_input}\nOutput:"
    
    async with SwarmClient(port=hub_port) as client:
        task_id = await client.add_task(full_prompt, task_type="chat")
        
        # Poll
        while True:
            await asyncio.sleep(0.5)
            status = await client._send_request("list", {"limit": 10}) 
            for t in status.get('tasks', []):
                if t['task_id'] == task_id and t['status'] == 'done':
                    return t['result']

async def bar_loop():
    # 1. Setup
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass
        
    print("🚀 Opening the Kirosu Bar... (Setting up agents)")
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH], "Hub"
    )
    
    # Wait for Hub
    for _ in range(20):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", HUB_PORT)
            writer.close()
            await writer.wait_closed()
            break
        except Exception:
            await asyncio.sleep(0.5)
    else:
        print("❌ Hub failed.")
        return

    # Start 4 Generic Agents (They will roleplay based on prompt)
    agents = []
    for i in range(4):
        p = start_process(
            [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", f"patron_{i}", "--model", "gpt-5.1-codex-mini"],
            f"Agent_{i}"
        )
        agents.append(p)
    
    print("🍺 Bar is open! The Patrons are capable of anything.")
    print("   (3 Drunks + 1 Sober Bartender to make sense of them)")
    print("-------------------------------------------------------")
    
    # Personas
    personas = [
        ("Drunk Philosopher", "You are a drunk philosopher. You speak in riddles, hiccups, and profound but confusing metaphors."),
        ("Angry Poet", "You are an angry poet. You rhyme aggressively and complain about the noise."),
        ("Confused Tourist", "You are a lost tourist who just wants to find the bathroom but keeps interrupting conversation.")
    ]
    
    bartender_persona = "You are a sober, tired bartender. Summarize what these three crazy people said into one clear, sane sentence for the user."

    while True:
        try:
            topic = input("\n\033[1mThow a topic to the bar\033[0m: ")
        except EOFError:
            break
        if topic.lower() in ["quit", "exit"]:
            break
            
        print(f"\n... The patrons are shouting about '{topic}' ...\n")
        
        # 1. Parallel Execution: Run all 3 drunks at once
        tasks = []
        for name, prompt in personas:
            # Pass HUB_PORT (new client per task) to avoid read-race on single socket
            tasks.append(run_agent_task(HUB_PORT, name, prompt, topic))
        
        # Wait for all 3
        results = await asyncio.gather(*tasks)
        
        patron_output = ""
        for (name, _), result in zip(personas, results):
            print(f"🍺 \033[33m{name}\033[0m: {result}")
            patron_output += f"{name}: {result}\n"
            
        print("\n... The Bartender (Formatter) is clearing his throat ...")
        
        # 2. Sequential Execution: Bartender cleans it up
        final_summary = await run_agent_task(HUB_PORT, "Bartender", bartender_persona, f"Here is what they said:\n{patron_output}")
        
        print(f"🍸 \033[1;32mBartender\033[0m: {final_summary}")

    # Cleanup
    print("\n👋 Closing Time!")
    hub.terminate()
    for a in agents: a.terminate()
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass

if __name__ == "__main__":
    try:
        asyncio.run(bar_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
        sys.exit(0)
