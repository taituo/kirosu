import asyncio
import json
import logging
import uuid
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("SwarmClient")

class SwarmClient:
    """
    A simple async client to interact with the Kirosu Hub via TCP/JSONL.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        logger.debug("Connected to Hub")

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Any:
        if not self.writer:
            await self.connect()
        
        req_id = str(uuid.uuid4())
        req = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id
        }
        self.writer.write((json.dumps(req) + "\n").encode())
        await self.writer.drain()

        # Read response
        while True:
            line = await self.reader.readline()
            if not line:
                raise ConnectionError("Connection closed")
            
            resp = json.loads(line)
            if resp.get("id") == req_id:
                if resp.get("error"):
                    raise RuntimeError(f"RPC Error: {resp['error']}")
                return resp.get("result")
            # Ignore unrelated messages (like keepalives if implemented)

    async def add_task(self, prompt: str, task_type: str = "chat") -> str:
        """Adds a task and returns its ID."""
        resp = await self._send_request("enqueue", {
            "prompt": prompt,
            "type": task_type,
            "context": {}
        })
        return resp['task_id']

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Gets task details."""
        resp = await self._send_request("list", {"limit": 100})
        tasks = resp.get("tasks", [])
        for t in tasks:
            if t.get('task_id') == task_id:
                return t
        raise ValueError("Task not found")

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
