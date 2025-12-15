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
from textual.message import Message

from kirosu.client import SwarmClient

# ---------------- CONFIG ----------------
HUB_PORT = 8793
DB_PATH = "lynx_dsl.db"

# ----------------- HELPERS -----------------
def start_process(cmd, name):
    return subprocess.Popen(
        cmd, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL, 
        env=os.environ.copy()
    )

class Link(Button):
    """A clickable link that looks like [1] Link Text."""
    def __init__(self, idx: int, text: str, url: str):
        super().__init__(f"[{idx}] {text}", id=f"link-{idx}", variant="primary")
        self.url = url
        self.idx = idx
        self.styles.width = "100%"
        self.styles.text_align = "left"
        self.styles.background = "#0000aa" # Lynx Blue
        self.styles.color = "#ffffff"
        self.styles.border = None

class BrowserContent(VerticalScroll):
    """The main scrolling area."""
    pass

class LynxApp(App):
    CSS = """
    Screen {
        background: #000000;
        color: #cccccc;
    }
    
    Header {
        background: #0000aa;
        color: #ffffff;
        dock: top;
    }

    Footer {
        background: #0000aa;
        color: #ffffff;
        dock: bottom;
    }
    
    #url-bar {
        dock: top;
        background: #333333;
        color: #ffffff;
        border: solid #0000aa;
    }
    
    BrowserContent {
        height: 1fr;
        padding: 1;
    }
    
    Label {
        padding-bottom: 1;
    }
    
    .status-bar {
        background: #0000aa; 
        color: #ffffff; 
        height: 1; 
        dock: bottom;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "back", "Back"),
        Binding("delete", "back", "Back"), # Backspace often maps to delete in terminals
        Binding("r", "reload", "Reload"),
        Binding("tab", "focus_next", "Next Link"),
        Binding("down", "focus_next", "Next Link"),
        Binding("shift+tab", "focus_previous", "Prev Link"),
        Binding("up", "focus_previous", "Prev Link"),
        Binding("a", "add_bookmark", "Add Bookmark"),
        Binding("v", "view_bookmarks", "View Bookmarks"),
    ]

    current_url = reactive("http://www.yahoo.com")
    history: List[str] = []
    bookmarks: List[str] = ["http://www.yahoo.com", "http://www.altavista.digital.com"]
    
    def __init__(self):
        super().__init__()
        self.client_proc = None
        self.agent_proc = None
        self.hub_proc = None
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Input(placeholder="URL or G for Gopher...", id="url-bar")
        yield BrowserContent(id="content-area")
        yield Label("Ready.", id="status-bar", classes="status-bar")
        yield Footer()

    async def on_mount(self):
        self.title = "Lynx 2.7.1 (DSL Connection)"
        # Spin up infrastructure
        self.query_one("#status-bar", Label).update("Initializing TCP/IP...")
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
        self.agent_proc = start_process(
             [sys.executable, "-m", "kirosu.cli", "agent", "--port", str(HUB_PORT), "--id", "WEB", "--model", "gpt-5.1-codex-mini"], 
             "Agent"
        )
        time.sleep(2)

    def action_back(self):
        if len(self.history) > 1:
            self.history.pop() # Current
            prev = self.history.pop() # Target
            asyncio.create_task(self.load_page(prev, record_history=False))
        else:
            self.notify("Already at start of history")

    def action_add_bookmark(self):
        if self.current_url not in self.bookmarks:
            self.bookmarks.append(self.current_url)
            self.notify(f"Bookmarked: {self.current_url}")
        else:
            self.notify("Already bookmarked!")

    def action_view_bookmarks(self):
        asyncio.create_task(self.load_page("lynx://bookmarks"))

    async def load_page(self, url, record_history=True):
        if record_history and (not self.history or self.history[-1] != url):
            self.history.append(url)
            
        self.current_url = url
        self.query_one("#url-bar", Input).value = url
        content_area = self.query_one("#content-area")
        status = self.query_one("#status-bar", Label)
        
        # Clear old content
        await content_area.remove_children()
        
        # Handle Internal Pages
        if url == "lynx://bookmarks":
            status.update("Viewing Bookmarks List")
            result = "# 🔖 Bookmarks Page\n\n"
            for bm in self.bookmarks:
                 result += f"* [Go to {bm}]({bm})\n"
            result += "\n[Return to Yahoo](http://www.yahoo.com)"
            self.render_content(result)
            return

        status.update(f"Dialing {url}...")
        
        # Simulate Network
        try:
            # Retry connection logic
            connected = False
            for _ in range(5):
                 try:
                     async with SwarmClient(port=HUB_PORT) as client:
                        connected = True
                        prompt = f"""
You are the World Wide Web in 1997.
User visited: {url}
Generate a web page text.
Format LINKS as [Link Text](target_url).
Format IMAGES as [IMG: filename.gif].
Style: Geocities, Nerdy, 1997 aesthetics.
Content Type: Raw Text mixed with Links.
"""
                        full_prompt = f"System: You are a 1997 Web Server.\nRequest: {prompt}"
                        
                        task_id = await client.add_task(full_prompt, task_type="web")
                        result = None
                        for _ in range(30): # 15s timeout
                             await asyncio.sleep(0.5)
                             st = await client._send_request("list", {"limit": 5})
                             for t in st.get("tasks", []):
                                 if t["task_id"] == task_id and t["status"] == "done":
                                     result = t["result"]
                                     break
                             if result: break
                        
                        if not result:
                            result = "408 Request Timeout (Server busy)"
                        break # Success
                 except Exception:
                     await asyncio.sleep(1)
            
            if not connected:
                 result = "503 Service Unavailable (No Carrier - Hub Offline)"

        except Exception as e:
            result = f"500 Internal Error: {e}"

        # Parse and Render
        status.update("Rendering...")
        self.render_content(result or "No Data")
        status.update("Done. Press 'a' to bookmark.")

    def render_content(self, text):
        container = self.query_one("#content-area")
        
        # Split by links [Text](Url)
        parts = re.split(r'(\[[^\]]+\]\([^)]+\))', text)
        
        link_idx = 1
        for part in parts:
            link_match = re.match(r'\[([^\]]+)\]\(([^)]+)\)', part)
            if link_match:
                name = link_match.group(1)
                url = link_match.group(2)
                # Create Button Link
                btn = Link(link_idx, name, url)
                container.mount(btn)
                link_idx += 1
            else:
                # Regular Text
                if part.strip():
                    container.mount(Label(part))
        
        # Auto-focus first link if exists
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
        # Cleanup
        if self.agent_proc: self.agent_proc.terminate()
        if self.hub_proc: self.hub_proc.terminate()
        subprocess.run(["pkill", "-f", f"port {HUB_PORT}"], check=False)

if __name__ == "__main__":
    app = LynxApp()
    app.run()
