from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Static, DataTable
from textual.reactive import reactive
from textual.binding import Binding
from rich.text import Text

from .agent import HubClient

@dataclass(frozen=True)
class DashboardSnapshot:
    online: bool
    stats: dict[str, int]
    tasks: list[dict[str, Any]]
    error: str | None = None

def fetch_dashboard_snapshot(host: str, port: int, limit: int = 20) -> DashboardSnapshot:
    try:
        client = HubClient(host, port)
        # We need to use client.call but handle potential connection errors gracefully
        # HubClient.call creates a new connection each time, which is fine for polling
        
        resp_stats = client.call("stats", {})
        stats = dict(resp_stats.get("stats", {}) or {})
        
        resp_list = client.call("list", {"limit": limit})
        tasks = list(resp_list.get("tasks", []) or [])
        
        # Normalize stat values to ints
        stats_norm: dict[str, int] = {}
        for k, v in stats.items():
            try:
                stats_norm[str(k)] = int(v)
            except Exception:
                continue
                
        return DashboardSnapshot(online=True, stats=stats_norm, tasks=tasks, error=None)
    except Exception as e:
        return DashboardSnapshot(online=False, stats={}, tasks=[], error=str(e))

class StatBox(Static):
    """A widget to display a single statistic."""
    value = reactive(0)

    def __init__(self, label: str, id: str, color: str = "white"):
        super().__init__(id=id)
        self.label = label
        self.color = color

    def compose(self) -> ComposeResult:
        yield Static(self.label, classes="stat-label")
        self.digits = Static(str(self.value), classes="stat-value")
        self.digits.styles.color = self.color
        yield self.digits

    def watch_value(self, new_value: int | str) -> None:
        if hasattr(self, "digits"):
            self.digits.update(str(new_value))

class KiroDash(App):
    """Kiro Swarm Control Dashboard."""

    CSS = """
    Screen {
        layout: vertical;
        background: #0f111a;
    }
    
    .stat-value {
        text-align: center;
        content-align: center middle;
        width: 100%;
        height: 1fr;
        text-style: bold;
    }

    .header-container {
        layout: horizontal;
        height: 3;
        margin-bottom: 1;
        border-bottom: solid #00b8ff;
        background: #1a1d2d;
    }

    .logo-box {
        width: 1fr;
        height: 100%;
        content-align: center middle;
        color: #00ff9f;
        text-style: bold;
    }

    .stat-grid {
        layout: grid;
        grid-size: 6; 
        grid-gutter: 1;
        height: 10;
        margin: 1;
    }

    StatBox {
        background: #1a1d2d;
        border: wide #00ff9f;
        padding: 1;
        align: center middle;
    }

    .stat-label {
        text-align: center;
        width: 100%;
        color: #a0a0a0;
        text-style: bold;
    }

    DataTable {
        height: 1fr;
        border: wide #00b8ff;
        margin: 1;
        background: #0f111a;
    }
    
    DataTable > .datatable--header {
        background: #1a1d2d;
        color: #00ff9f;
        text-style: bold;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh Now"),
    ]

    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        self.connected = False

    def compose(self) -> ComposeResult:
        with Container(classes="header-container"):
             yield Static("KIRO SWARM CONTROL", classes="logo-box")
        
        with Container(classes="stat-grid"):
            yield StatBox("QUEUED", id="stat-queued", color="#ffbd2e")
            yield StatBox("LEASED", id="stat-leased", color="#00b8ff")
            yield StatBox("DONE", id="stat-done", color="#00ff9f")
            yield StatBox("FAILED", id="stat-failed", color="#ff5f56")
            yield StatBox("STATUS", id="stat-status", color="#aaaaaa")

        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        self.title = "Kiro Swarm Control"
        self.table = self.query_one(DataTable)
        self.table.add_columns("ID", "Status", "Prompt", "Worker", "Result")
        self.table.cursor_type = "row"
        self.table.zebra_stripes = True
        self.set_interval(1.0, self.update_stats)

    def action_refresh(self) -> None:
        self.update_stats()

    def update_stats(self) -> None:
        snap = fetch_dashboard_snapshot(self.host, self.port, limit=20)
        if snap.online:
            s = snap.stats

            self.query_one("#stat-queued", StatBox).value = s.get("queued", 0)
            self.query_one("#stat-leased", StatBox).value = s.get("leased", 0)
            self.query_one("#stat-done", StatBox).value = s.get("done", 0)
            self.query_one("#stat-failed", StatBox).value = s.get("failed", 0)

            self.connected = True
            self.query_one("#stat-status", StatBox).value = "ONLINE"
            self.query_one("#stat-status", StatBox).digits.styles.color = "#00ff00"

            tasks = snap.tasks
            self.table.clear()
            for t in tasks:
                t_id = str(t["task_id"])
                status = t["status"]
                prompt = t["prompt"][:50].replace("\n", " ") + "..."
                worker = (t["worker_id"] or "-").split("-")[1] if "-" in (t["worker_id"] or "") else "-"
                result = (t["result"] or "")[:50].replace("\n", " ") + "..."

                if status == "done":
                    status_styled = "[bold green]✔ DONE[/]"
                elif status == "failed":
                    status_styled = "[bold red]✘ FAIL[/]"
                elif status == "leased":
                    status_styled = "[bold cyan]⟳ RUN [/]"
                elif status == "queued":
                    status_styled = "[bold yellow]● WAIT[/]"
                else:
                    status_styled = status

                self.table.add_row(t_id, status_styled, prompt, worker, result)
        else:
            self.connected = False
            self.query_one("#stat-status", StatBox).value = "OFFLINE"
            self.query_one("#stat-status", StatBox).digits.styles.color = "#ff0000"

def run_dashboard(host: str, port: int):
    app = KiroDash(host, port)
    app.run()
