from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
import uuid
from typing import Any

from .config import get_agent_config


class HubClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.sock = None
        self.f = None
        self.auth_token = os.environ.get("KIRO_SWARM_KEY")

    def _connect(self):
        if self.sock:
            return
        self.sock = socket.create_connection((self.host, self.port))
        self.f = self.sock.makefile("r")

    def _disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
            self.f = None

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req_id = str(uuid.uuid4())
        params = params or {}
        if self.auth_token:
            params["auth_token"] = self.auth_token
            
        req = {"id": req_id, "method": method, "params": params}
        
        # Simple retry logic for persistent connection
        for attempt in range(2):
            try:
                self._connect()
                if not self.sock or not self.f:
                    raise RuntimeError("Failed to connect")
                    
                self.sock.sendall((json.dumps(req) + "\n").encode("utf-8"))
                line = self.f.readline()
                if not line:
                    self._disconnect()
                    if attempt == 0:
                        continue # Reconnect and retry
                    raise RuntimeError("Empty response from hub")
                    
                resp = json.loads(line)
                if resp.get("error"):
                    raise RuntimeError(f"Hub error: {resp['error']}")
                return resp["result"]
            except (BrokenPipeError, ConnectionResetError):
                self._disconnect()
                if attempt == 0:
                    continue
                raise


from .providers import get_provider

class KiroAgent:
    def __init__(self, host: str, port: int, model: str | None = None, workdir: str | None = None, agent_name: str | None = None):
        self.client = HubClient(host, port)
        self.worker_id = f"kiro-{uuid.uuid4().hex[:8]}"
        
        # Load config
        config = get_agent_config(agent_name) if agent_name else {}
        
        self.model = model or config.get("model") or os.environ.get("MITTELO_KIRO_MODEL", "claude-haiku-4.5")
        self.workdir = workdir or config.get("workdir")
        
        # Initialize Provider
        provider_name = os.environ.get("KIRO_PROVIDER")
        self.provider = get_provider(provider_name, self.model)

    def run_loop(self, poll_interval: float = 1.0, log_file: str | None = None, verbose: bool = False):
        level = logging.DEBUG if verbose else logging.INFO
        handlers = [logging.StreamHandler()]
        if log_file:
            handlers.append(logging.FileHandler(log_file))
            
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=handlers,
            force=True
        )
        logging.info(f"Agent {self.worker_id} started. Connecting to {self.client.host}:{self.client.port}")
        while True:
            try:
                self._tick()
            except Exception as e:
                logging.error(f"Error in agent loop: {e}")
            time.sleep(poll_interval)

    def _tick(self):
        # Lease 1 task
        resp = self.client.call("lease", {"worker_id": self.worker_id, "max_tasks": 1, "lease_seconds": 300})
        tasks = resp.get("tasks", [])
        if not tasks:
            return

        task = tasks[0]
        task_id = task["task_id"]
        prompt = task["prompt"]
        system_prompt = task.get("system_prompt")
        task_type = task.get("type", "chat")
        
        # Context Injection
        context_file = os.path.join(self.workdir or os.getcwd(), ".kiro", "context.md")
        if os.path.exists(context_file):
            try:
                with open(context_file, "r") as f:
                    context_content = f.read()
                system_prompt = f"{context_content}\n\n{system_prompt}" if system_prompt else context_content
                logging.info(f"Injected context from {context_file}")
            except Exception as e:
                logging.warning(f"Failed to load context file: {e}")
        
        logging.info(f"Leased task {task_id} ({task_type}): {prompt[:50]}...")
        
        try:
            if task_type == "python":
                result = self._run_python(prompt)
            else:
                # Use Provider
                result = self.provider.run(prompt, system_prompt, self.workdir)
                
            self.client.call("ack", {"task_id": task_id, "status": "done", "result": result})
            logging.info(f"Task {task_id} done.")
            logging.debug(f"Task {task_id} result:\n{result}")
        except Exception as e:
            error_msg = str(e)
            self.client.call("ack", {"task_id": task_id, "status": "failed", "error": error_msg})
            logging.error(f"Task {task_id} failed: {error_msg}")

    def _run_python(self, code: str) -> str:
        # DANGEROUS: Runs arbitrary Python code
        logging.warning("Executing DANGEROUS Python code")
        
        cmd = ["python3", "-c", code]
        
        env = os.environ.copy()
        
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=env,
            cwd=self.workdir
        )
        
        if process.returncode != 0:
            msg = (process.stderr or process.stdout or "").strip()
            raise RuntimeError(f"Python execution failed (code {process.returncode}): {msg}")
            
        return process.stdout or ""
