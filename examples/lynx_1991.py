import asyncio
import logging
import os
import sys
import subprocess
import time
import random
import re
from typing import Dict, Optional, List
from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
logging.basicConfig(level=logging.ERROR)
logging.getLogger("SwarmClient").setLevel(logging.ERROR)
logging.getLogger("root").setLevel(logging.ERROR)

HUB_PORT = 8792
DB_PATH = "lynx.db"

# ----------------- BROWSER ENGINE -----------------

class LynxBrowser:
    def __init__(self):
        self.history = []
        self.current_url = "gopher://home"
        self.links: Dict[int, str] = {} # Map [1] -> URL
        self.cache: Dict[str, str] = {} # URL -> Page Content
        
    def _render_page(self, raw_content: str):
        """
        Parses the raw content, finds links [Link Name](TARGET), and renders as Lynx.
        Returns the visible text and updates self.links.
        """
        self.links = {}
        rendered_lines = []
        link_counter = 1
        
        # Regex for markdown links [Text](URL)
        # We replace them with [N] Text
        
        def replace_link(match):
            nonlocal link_counter
            text = match.group(1)
            url = match.group(2)
            idx = link_counter
            self.links[idx] = url
            link_counter += 1
            return f"[{idx}] {text}"

        processed_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, raw_content)
        
        return processed_text

    async def fetch(self, url: str, client: SwarmClient) -> str:
        self.current_url = url
        if url in self.cache:
            return self._render_page(self.cache[url])
            
        # Simulate Modem Latency
        print(f"\nDialing {url}...", end="", flush=True)
        for _ in range(3):
            await asyncio.sleep(0.2)
            print(".", end="", flush=True)
        print(" Connected (2400 baud).")
        
        # Generate via LLM
        prompt = f"""
You are the World Wide Web in 1997. Limit 500 chars.
User visited: {url}
Generate a simpler text-mode web page suitable for Lynx.
Use Markdown links like [Link Name](target_url).
Style: "Under Construction" banners (represented as text), WebRings, Guestbooks, Hit Counters.
Topics: X-Files, Spice Girls, GeoCities Neighborhoods, AltaVista, Netscape N-logo.
Formatting: Use [IMG: animated_mailbox.gif] placeholders.
Context: It is 1997. CSS doesn't exist yet. Tables are used for layout.
"""
        resp = await ask_dm(client, "You are a 1997 Web Server.", prompt)
        
        self.cache[url] = resp
        return self._render_page(resp)

# ----------------Kirosu Helpers ----------------

def start_process(cmd, name):
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, # Silence stderr for immersion
        env=os.environ.copy()
    )

async def ask_dm(client, system_context, player_input):
    full_prompt = f"System: {system_context}\nTask: {player_input}"
    task_id = await client.add_task(full_prompt, task_type="game")
    while True:
        await asyncio.sleep(0.3)
        status = await client._send_request("list", {"limit": 5}) 
        for t in status.get('tasks', []):
            if t['task_id'] == task_id and t['status'] == 'done':
                return t['result']

# ---------------- MAIN LOOP ----------------

async def game_loop():
    # Setup
    if os.path.exists(DB_PATH):
        try: os.remove(DB_PATH)
        except: pass
        
    print("📠 Initializing TCP/IP Stack... ", end="", flush=True)
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    
    hub = start_process(
        [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH], "Hub"
    )
    time.sleep(1) # Fast boot
    print("OK.")

    print("📠 Dialing ISP... ", end="", flush=True)
    # Start Agent
    agent = start_process(
        [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "LYNX", "--model", "gpt-5.1-codex-mini"],
        "Web"
    )
    time.sleep(3)
    print("CONNECTED.")
    
    browser = LynxBrowser()
    
    # Pre-seed Home (1997 Style)
    browser.cache["http://www.yahoo.com"] = """
# Yahoo!

**My Personal Guide to the Internet**

[Search] [Options]

* [Arts & Humanities](http://yahoo.com/arts)
* [Computers & Internet](http://yahoo.com/computers)
* [Entertainment](http://yahoo.com/ent) (X-Files, Titanic)
* [Geocities - Create your Home Page](http://www.geocities.com)
* [AltaVista Search](http://www.altavista.digital.com)

(C) 1997 Yahoo! Inc. - "Do You Yahoo!?"
[Text-Only Mode]
"""

    async with SwarmClient(port=HUB_PORT) as client:
        # Initial Render
        content = browser._render_page(browser.cache["http://www.yahoo.com"])
        
        while True:
            # 🖥️ FULL SCREEN UI 🖥️
            # Clear Screen + Home Cursor
            print("\033[2J\033[H", end="") 
            
            # Header
            print("\033[1;37;44m" + f" Lynx 2.7.1   URL: {browser.current_url}".ljust(80) + "\033[0m")
            
            # Content Area (20 lines max)
            lines = content.split('\n')
            for i in range(20):
                if i < len(lines):
                    print(f" {lines[i]}")
                else:
                    print("") # Empty padding
            
            # Footer
            print("\033[1;37;44m" + " Commands: [N] Follow Link  [Q] Quit  [G] Go URL".ljust(80) + "\033[0m")
            
            try:
                cmd = input("\n\033[1mLynx> \033[0m").strip().lower()
            except EOFError: break
            
            if cmd in ['q', 'quit', 'exit']: break
            
            # Handle Link Numbers
            if cmd.isdigit():
                idx = int(cmd)
                if idx in browser.links:
                    url = browser.links[idx]
                    content = await browser.fetch(url, client)
                else:
                    print(f"❌ Error 404: Link [{idx}] not found.")
                    await asyncio.sleep(1)
            elif cmd.startswith('g ') or cmd.startswith('u '):
                url = cmd.split(' ', 1)[1]
                content = await browser.fetch(url, client)
            elif cmd == 'b':
                print("Back functionality not implemented in v1.0 beta")
                await asyncio.sleep(1)
            else:
                 # Interactive Search or "Surfing"
                 content = await browser.fetch(f"search://{cmd}", client)

    # Cleanup
    hub.terminate()
    agent.terminate()
    subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
    if os.path.exists(DB_PATH): os.remove(DB_PATH)

if __name__ == "__main__":
    try:
        asyncio.run(game_loop())
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nNO CARRIER")
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
