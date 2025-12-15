import asyncio
import logging
import os
import sys
import subprocess
import time
from kirosu.client import SwarmClient

# Configure minimal logging
logging.basicConfig(level=logging.ERROR)

HUB_PORT = 8790
DB_PATH = "chat_demo.db"

def start_process(cmd, name):
    # Quiet start but allow stderr for debug
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=sys.stderr, # PIPE error to main process stderr
        env=os.environ.copy()
    )

async def chat_loop():
    # 1. Setup
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    print("🚀 Starting Kirosu Chat Backend...")
    # Kill zombies first
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH],
        "Hub"
    )
    
    # Wait for Hub to be ready (robustness)
    print("Waiting for Hub...", end="", flush=True)
    for _ in range(20):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", HUB_PORT)
            writer.close()
            await writer.wait_closed()
            print(" Connected!")
            break
        except Exception:
            print(".", end="", flush=True)
            await asyncio.sleep(0.5)
    else:
        print("\n❌ Hub failed to start!")
        hub.terminate()
        return

    agent = start_process(
        [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "chat_bot", "--model", "gpt-5.1-codex-mini"],
        "Agent"
    )
    time.sleep(2) # Agent needs a moment to register
    
    print("\n💬 Kirosu Chatbot Ready! (Type 'quit' to exit)")
    print("---------------------------------------------")

    # 2. State Management (Client-Side History)
    history = []
    
    async with SwarmClient(port=HUB_PORT) as client:
        while True:
            try:
                user_text = input("You: ")
            except EOFError:
                break
                
            if user_text.lower() in ["quit", "exit"]:
                break
            
            # 3. Construct Context-Aware Prompt
            # We explicitly feed the history back to the stateless agent each time.
            system_prompt = "You are a helpful, witty AI assistant."
            formatted_history = "\n".join([f"{role}: {msg}" for role, msg in history])
            full_prompt = f"{formatted_history}\nUser: {user_text}\nAssistant:"
            
            try:
                # 4. Execute Task (Single Turn)
                # The agent doesn't "remember", we "remind" it.
                print("... (thinking) ...", end="\r")
                task_id = await client.add_task(full_prompt, task_type="chat")
                
                # Poll for result
                result = None
                while result is None:
                    # Polling wait to avoid spam
                    await asyncio.sleep(0.5)

                    status = await client._send_request("list", {"limit": 1})
                    # In real app use get_task(id)
                    for t in status.get('tasks', []):
                        if t['task_id'] == task_id and t['status'] == 'done':
                            result = t['result']
                            break
                
                print(f"Bot: {result}")
                
                # 5. Update State
                history.append(("User", user_text))
                history.append(("Assistant", result))
                
            except Exception as e:
                print(f"Error: {e}")

    # Cleanup
    hub.terminate()
    agent.terminate()
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass

if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except KeyboardInterrupt:
        pass
