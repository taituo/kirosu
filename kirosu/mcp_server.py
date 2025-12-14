import asyncio
import os
import logging
from typing import Any
from mcp.server.fastmcp import FastMCP

from .agent import HubClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kiro-mcp")

# Initialize FastMCP
mcp = FastMCP("kiro-swarm")

def get_client() -> HubClient:
    host = os.environ.get("KIRO_SWARM_HOST", "127.0.0.1")
    port = int(os.environ.get("KIRO_SWARM_PORT", "8765"))
    return HubClient(host, port)

@mcp.tool()
def enqueue_task(prompt: str, system_prompt: str | None = None, task_type: str = "chat") -> str:
    """
    Enqueue a new task to the Kiro Swarm.
    
    Args:
        prompt: The main instruction for the agent.
        system_prompt: Optional system prompt/persona.
        task_type: Type of task ("chat" or "python").
    """
    client = get_client()
    try:
        resp = client.call("enqueue", {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "type": task_type
        })
        return f"Task enqueued with ID: {resp['task_id']}"
    except Exception as e:
        return f"Error enqueuing task: {str(e)}"

@mcp.tool()
def list_tasks(status: str | None = None, limit: int = 10) -> str:
    """
    List tasks in the swarm.
    
    Args:
        status: Filter by status (queued, leased, done, failed).
        limit: Max number of tasks to return.
    """
    client = get_client()
    try:
        resp = client.call("list", {"status": status, "limit": limit})
        tasks = resp.get("tasks", [])
        if not tasks:
            return "No tasks found."
        
        output = []
        for t in tasks:
            output.append(f"ID: {t['task_id']} | Status: {t['status']} | Type: {t.get('type', 'chat')} | Prompt: {t['prompt'][:30]}...")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing tasks: {str(e)}"

@mcp.tool()
def get_task_status(task_id: int) -> str:
    """
    Get the detailed status and result of a specific task.
    
    Args:
        task_id: The ID of the task.
    """
    client = get_client()
    try:
        # We don't have a direct get_task method, so we list with limit=100 and filter (inefficient but works for now)
        # Or better, we can assume list returns recent ones. 
        # Ideally we should add get_task to Hub, but for now let's use list.
        # Actually, let's just implement a simple filter on the client side for now.
        resp = client.call("list", {"limit": 100})
        tasks = resp.get("tasks", [])
        task = next((t for t in tasks if t["task_id"] == task_id), None)
        
        if not task:
            return f"Task {task_id} not found (or not in recent 100)."
            
        return (
            f"Task ID: {task['task_id']}\n"
            f"Status: {task['status']}\n"
            f"Type: {task.get('type', 'chat')}\n"
            f"Prompt: {task['prompt']}\n"
            f"Result: {task.get('result')}\n"
            f"Error: {task.get('error')}"
        )
    except Exception as e:
        return f"Error getting task status: {str(e)}"

def run_mcp_server():
    """Run the MCP server."""
    mcp.run()
