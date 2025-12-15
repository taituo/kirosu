from __future__ import annotations
import sys
import os
import asyncio
import subprocess
import time
import re
from typing import Dict, List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Static, Input, Button, Label
from textual.binding import Binding
from textual.reactive import reactive

from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
HUB_PORT = 8794
DB_PATH = "real_browser.db"

# ----------------- HELPERS -----------------
def start_process(cmd, name, env=None):
    environ = os.environ.copy()
    if env: environ.update(env)
    
    # Log to file for debugging
    log_file = open(f"{name.lower()}_debug.log", "w")
    return subprocess.Popen(
        cmd, 
        stdout=log_file, 
        stderr=log_file, 
        env=environ
    )

class Link(Button):
    def __init__(self, idx: int, text: str, url: str):
        super().__init__(f"[{idx}] {text}", id=f"link-{idx}", variant="primary")
        self.url = url
        self.idx = idx
        self.styles.width = "100%"
        self.styles.text_align = "left"
        self.styles.background = "#0000aa" 
        self.styles.color = "#ffffff"
        self.styles.border = None

class BrowserContent(VerticalScroll):
    pass

class RealBrowserApp(App):
    CSS = """
    Screen { background: #000000; color: #cccccc; }
    Header { background: #0000aa; color: #ffffff; dock: top; }
    Footer { background: #0000aa; color: #ffffff; dock: bottom; }
    #url-bar { dock: top; background: #333333; color: #ffffff; border: solid #0000aa; }
    BrowserContent { height: 1fr; padding: 1; }
    Label { padding-bottom: 1; }
    .status-bar { background: #0000aa; color: #ffffff; height: 1; dock: bottom; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "back", "Back"),
        Binding("r", "reload", "Reload"),
        Binding("tab", "focus_next", "Next Link"),
        Binding("shift+tab", "focus_previous", "Prev Link"),
        Binding("up", "focus_previous", "Prev Link"),
        Binding("down", "focus_next", "Next Link"),
    ]

    current_url = reactive("http://www.google.com")
    history: List[str] = []
    
    def __init__(self):
        super().__init__()
        self.client_proc = None
        self.agent_proc = None
        self.hub_proc = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Input(placeholder="URL or Query...", id="url-bar")
        yield BrowserContent(id="content-area")
        yield Label("Ready.", id="status-bar", classes="status-bar")
        yield Footer()

    async def on_mount(self):
        self.title = "Kiro RealBrowser 1.0"
        self.query_one("#status-bar", Label).update("Initializing AI Engine...")
        self.start_infrastructure()
        await self.load_page(self.current_url)

    def start_infrastructure(self):
        # Kill old
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        
        self.hub_proc = start_process(
             [sys.executable, "-m", "kirosu.cli", "hub", "--port", str(HUB_PORT), "--db", DB_PATH], "Hub"
        )
        time.sleep(1)
        
        # ENABLE SEARCH via KIRO-CLI (User said it works out of the box)
        # We switch provider environmental variable logic in kirosu.cli.agent indirectly
        # Actually easier to just force KIRO_PROVIDER env var for the subprocess
        env = {"KIRO_PROVIDER": "kiro-cli"} 
        
        self.agent_proc = start_process(
             [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "WEB", "--model", "claude-haiku-4.5"], 
             "Agent",
             env=env
        )
        time.sleep(2)

    def action_back(self):
        if len(self.history) > 1:
            self.history.pop() 
            prev = self.history.pop() 
            asyncio.create_task(self.load_page(prev, record_history=False))

    async def load_page(self, url, record_history=True):
        if record_history and (not self.history or self.history[-1] != url):
            self.history.append(url)
            
        self.current_url = url
        self.query_one("#url-bar", Input).value = url
        content_area = self.query_one("#content-area")
        status = self.query_one("#status-bar", Label)
        
        await content_area.remove_children()
        status.update(f"Searching/Fetching {url}...")
        
        # Simulate Network
        try:
            connected = False
            for _ in range(5):
                 try:
                     async with SwarmClient(port=HUB_PORT) as client:
                        connected = True
                        # PROMPT FOR REAL BROWSING (Strict "Business" Mode to avoid refusals)
                        prompt = f"""
PERFORM WEB RETRIEVAL TASK:
Target: {url}

INSTRUCTIONS:
1. Use your available tools (search / fetch) to get information about the Target.
2. If it is a URL, visit it. If it is a query, search for it.
3. OUTPUT FORMAT: Markdown.
   - Title of the page/result.
   - Concise summary of the main content (max 500 chars).
   - List of key links found as [Link Text](URL).
4. CONSTRAINT: Do NOT ask clarifying questions. Do NOT refuse. Just provide the data found.
"""
                        full_prompt = f"System: You are a Web Retrieval Agent.\nRequest: {prompt}"
                        
                        task_id = await client.add_task(full_prompt, task_type="web")
                        result = None
                        
                        # Logging
                        with open("browser_debug.log", "a") as log:
                            log.write(f"[{time.time()}] Task {task_id} started because user requested {url}\n")
                        
                        for _ in range(120): # 60s timeout (Real search takes time)
                             await asyncio.sleep(0.5)
                             st = await client._send_request("list", {"limit": 5})
                             for t in st.get("tasks", []):
                                 if t["task_id"] == task_id:
                                     if t["status"] == "done":
                                         result = t["result"]
                                         break
                                     elif t["status"] == "failed":
                                         result = "500 Agent Failed (Check browser_debug.log)"
                                         break
                             if result: break
                        
                        if not result: 
                            result = "408 Request Timeout (Agent took too long searching)"
                            with open("browser_debug.log", "a") as log:
                                log.write(f"[{time.time()}] Task {task_id} timed out.\n")
                        else:
                            with open("browser_debug.log", "a") as log:
                                log.write(f"[{time.time()}] Task {task_id} finished. Len: {len(result)}\n")
                        
                        break 
                 except Exception:
                     await asyncio.sleep(1)
            
            if not connected: result = "503 Hub Offline"

        except Exception as e: result = f"Error: {e}"

        status.update("Rendering...")
        self.render_content(result or "No Data")
        status.update("Done.")

    def render_content(self, text):
        container = self.query_one("#content-area")
        parts = re.split(r'(\[[^\]]+\]\([^)]+\))', text)
        link_idx = 1
        for part in parts:
            link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part)
            if link_match:
                name = link_match.group(1)
                url = link_match.group(2)
                btn = Link(link_idx, name, url)
                container.mount(btn)
                link_idx += 1
            else:
                if part.strip(): container.mount(Label(part))
        
        try:
             first_btn = container.query("Link").first()
             if first_btn: first_btn.focus()
        except: pass

    async def on_button_pressed(self, event: Button.Pressed):
        if isinstance(event.button, Link):
            await self.load_page(event.button.url)
            
    async def on_input_submitted(self, event: Input.Submitted):
        url = event.value
        await self.load_page(url)

    def on_unmount(self):
        if self.agent_proc: self.agent_proc.terminate()
        if self.hub_proc: self.hub_proc.terminate()
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)

if __name__ == "__main__":
    app = RealBrowserApp()
    app.run()
