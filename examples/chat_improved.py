import asyncio
import logging
import os
import sys
import subprocess
import time
from kirosu.client import SwarmClient

# Configure minimal logging
# Configure logging to suppress INFO noise from libraries
# Configure logging to suppress INFO noise from libraries
logging.basicConfig(level=logging.ERROR)
# Silence internal loggers
logging.getLogger("SwarmClient").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

HUB_PORT = 8790
DB_PATH = "chat_demo.db"

def start_process(cmd, name):
    # Quiet start, silence EVERYTHING
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, # No errors either
        env=os.environ.copy()
    )

async def typing_animation(event):
    """Shows a 'Bot is typing...' animation until event is set."""
    chars = [".  ", ".. ", "...", "   "]
    idx = 0
    while not event.is_set():
        sys.stdout.write(f"\rBot is typing {chars[idx]}")
        sys.stdout.flush()
        idx = (idx + 1) % len(chars)
        await asyncio.sleep(0.3)
    sys.stdout.write("\r" + " " * 20 + "\r") # Clear line

async def chat_loop():
    # 1. Setup
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass
        
    print("🚀 Starting Kirosu Chat Backend (Hidden)...")
    # Kill zombies first
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    
    # Start Hub (silently)
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH],
        "Hub"
    )
    
    # Wait for Hub to be ready
    for _ in range(20):
        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", HUB_PORT)
            writer.close()
            await writer.wait_closed()
            break
        except Exception:
            await asyncio.sleep(0.5)
    else:
        print("\n❌ Hub failed to start!")
        hub.terminate()
        return

    # Start Agent (silently)
    agent = start_process(
        [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "chat_bot", "--model", "gpt-5.1-codex-mini"],
        "Agent"
    )
    time.sleep(3) # Give agent time to ensure subscription (silent wait)
    
    print("\n" + "="*50)
    print(" 🤖 Kirosu Chat Ready")
    print(" Type 'quit' to exit.")
    print("="*50 + "\n")

    # 2. State Management (Client-Side History)
    history = []
    
    async with SwarmClient(port=HUB_PORT) as client:
        while True:
            try:
                user_text = input("\033[1mYou\033[0m: ")
            except EOFError:
                break
                
            if user_text.lower() in ["quit", "exit"]:
                break
            
            # 3. Construct Context-Aware Prompt
            formatted_history = "\n".join([f"{role}: {msg}" for role, msg in history])
            full_prompt = f"System: You are a helpful, witty AI assistant. Keep answers concise.\n\n{formatted_history}\nUser: {user_text}\nAssistant:"
            
            try:
                # 4. Execute Task
                done_event = asyncio.Event()
                spinner_task = asyncio.create_task(typing_animation(done_event))

                task_id = await client.add_task(full_prompt, task_type="chat")
                
                # Poll for result
                result = None
                while result is None:
                    await asyncio.sleep(0.5)
                    status = await client._send_request("list", {"limit": 1})
                    for t in status.get('tasks', []):
                        if t['task_id'] == task_id and t['status'] == 'done':
                            result = t['result']
                            break
                
                # Stop spinner
                done_event.set()
                await spinner_task
                
                print(f"\033[1mBot\033[0m: {result}\n")
                
                # 5. Update State
                history.append(("User", user_text))
                history.append(("Assistant", result))
                
            except Exception as e:
                print(f"Error: {e}")

    # Cleanup
    print("\n👋 Closing Chat...")
    hub.terminate()
    agent.terminate()
    # Force kill if needed
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass

if __name__ == "__main__":
    try:
        asyncio.run(chat_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        # Clean exit without traceback
        subprocess.run(["pkill", "-f", "port 8790"], check=False)
        sys.exit(0)
