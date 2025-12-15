from __future__ import annotations
import sys
import os
import asyncio
import subprocess
import time
import re
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Input, Button, Label, Digits
from textual.binding import Binding
from textual.reactive import reactive

from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
# Use a different port to avoid conflicts with other demos
HUB_PORT = 8795
DB_PATH = "teletext.db"

# ----------------- HELPERS -----------------
def start_process(cmd, name, env=None):
    environ = os.environ.copy()
    if env: environ.update(env)
    
    # Log to file for debugging
    log_file = open(f"{name.lower()}_tt_debug.log", "w")
    return subprocess.Popen(
        cmd, 
        stdout=log_file, 
        stderr=log_file, 
        env=environ
    )

class TeletextScreen(Static):
    """The 40x24 Grid Screen"""
    pass

class TeletextApp(App):
    CSS = """
    Screen {
        background: #000000;
        color: #ecf0f1;
        align: center middle;
    }
    
    TeletextScreen {
        width: 80; /* Textual uses columns, standard terminal font is roughly 1:2 aspect ratio so 80 cols is close to 40 chars visually? Or just simple text */
        height: 25;
        background: #000000;
        border: none;
        padding: 1;
        text-style: bold;
    }
    
    #header-bar {
        dock: top;
        height: 1;
        background: #000000;
        color: #ffffff;
    }

    #input-overlay {
        dock: bottom;
        height: 3;
        background: #111111;
        color: #00ff00;
        padding: 0 1;
        border-top: solid #00ff00;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("escape", "quit", "Quit"),
        Binding("number", "input_number", "Digit"),
    ]

    current_page = reactive("100")
    input_buffer = reactive("")
    page_cache: Dict[str, str] = {}
    
    # Predefined Routes for Authentic Experience
    ROUTES = {
        "100": "News Index / Etusivu",
        "101": "Domestic News / Kotimaa",
        "102": "International / Ulkomaat",
        "200": "Sports / Urheilu",
        "201": "Ice Hockey / Jääkiekko",
        "300": "Weather / Sää",
        "400": "Entertainment / Viihde",
        "666": "Horoscope / Ennusteet",
        "888": "Stock Market / Pörssi",
    }
    
    def __init__(self):
        super().__init__()
        self.client_proc = None
        self.agent_proc = None
        self.hub_proc = None
        
    def compose(self) -> ComposeResult:
        yield Label("P100  YLE TELETEXT  24.12. 12:00:00", id="header-bar")
        yield TeletextScreen(id="screen")
        yield Label("Page: 100", id="input-overlay")

    def on_key(self, event):
        if event.key in "0123456789":
            self.input_buffer += event.key
            self.query_one("#input-overlay", Label).update(f"Seek: {self.input_buffer}")
            if len(self.input_buffer) == 3:
                self.load_page(self.input_buffer)
                self.input_buffer = ""
        elif event.key == "backspace":
            self.input_buffer = self.input_buffer[:-1]
            self.query_one("#input-overlay", Label).update(f"Seek: {self.input_buffer}")

    async def on_mount(self):
        self.start_infrastructure()
        self.load_page("100")

    def start_infrastructure(self):
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        
        self.hub_proc = start_process(
             [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH], "Hub"
        )
        time.sleep(1)
        
        # Use Kiro CLI with Claude Haiku for search
        env = {"KIRO_PROVIDER": "kiro-cli"} 
        self.agent_proc = start_process(
             [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "TELETEXT", "--model", "claude-haiku-4.5"], 
             "Agent", 
             env=env
        )
        time.sleep(2)

    def load_page(self, page_num):
        self.current_page = page_num
        self.query_one("#header-bar", Label).update(f"P{page_num}  YLE TELETEXT  {time.strftime('%d.%m. %H:%M:%S')}")
        self.query_one("#input-overlay", Label).update(f"Loading {page_num}...")
        
        # Check predefined topic
        topic = self.ROUTES.get(page_num, f"Random Internet Page {page_num}")
        
        asyncio.create_task(self.fetch_content(page_num, topic))

    async def fetch_content(self, page_num, topic):
        screen = self.query_one("#screen", TeletextScreen)
        screen.update(f"\n\n    FETCHING PAGE {page_num}...\n    Target: {topic}\n\n    [Connecting to ANTENNA...]")
        
        # Determine query
        query = topic
        if page_num == "100":
            query = "Top News Headlines Finland International"
        
        try:
             async with SwarmClient(port=HUB_PORT) as client:
                prompt = f"""
TASK: FETCH AND FORMAT DATA
TOPIC: "{query}"

INSTRUCTIONS:
1. Search for real information about the TOPIC.
2. Format the output to fit a 40x24 character grid (Monospace).
3. STYLE: "YLE TEKSTI-TV" (Blocky, Uppercase, Telegraphic).
4. COLORS: Use tags like [bold magenta], [bold yellow], [bold cyan].
5. HEADER: P{page_num} YLE TELETEXT
6. FOOTER: 100 Uutiset  200 Urheilu  300 Sää

CONSTRAINT: Do NOT discuss your identity. Do NOT refuse. Just output the grid content.
"""
                full_prompt = f"System: You are an ASCII Data Formatter.\nRequest: {prompt}"
                
                # Fetch
                task_id = await client.add_task(full_prompt, task_type="web")
                result = None
                for _ in range(60): # 30s timeout
                     await asyncio.sleep(0.5)
                     st = await client._send_request("list", {"limit": 5})
                     for t in st.get("tasks", []):
                         if t["task_id"] == task_id and t["status"] == "done":
                             result = t["result"]
                             break
                     if result: break
                
                if not result: result = "[red]SIGNAL LOST (TIMEOUT)[/]"
                
                self.update_screen(result)
                self.query_one("#input-overlay", Label).update(f"Page {page_num} Loaded.")

        except Exception as e:
            self.update_screen(f"[red]CONNECTION ERROR[/]\n\n{e}")

    def update_screen(self, content):
        self.query_one("#screen", TeletextScreen).update(content)

    def on_unmount(self):
        if self.agent_proc: self.agent_proc.terminate()
        if self.hub_proc: self.hub_proc.terminate()
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)

if __name__ == "__main__":
    app = TeletextApp()
    app.run()
