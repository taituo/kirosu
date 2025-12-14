from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
import uuid
from typing import Any


class HubClient:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        req_id = str(uuid.uuid4())
        req = {"id": req_id, "method": method, "params": params or {}}
        
        with socket.create_connection((self.host, self.port)) as sock:
            sock.sendall((json.dumps(req) + "\n").encode("utf-8"))
            f = sock.makefile("r")
            line = f.readline()
            if not line:
                raise RuntimeError("Empty response from hub")
            resp = json.loads(line)
            
        if resp.get("error"):
            raise RuntimeError(f"Hub error: {resp['error']}")
        return resp["result"]


class KiroAgent:
    def __init__(self, hub_host: str, hub_port: int, model: str | None = None, workdir: str | None = None):
        self.client = HubClient(hub_host, hub_port)
        self.worker_id = f"kiro-{uuid.uuid4().hex[:8]}"
        self.model = model or os.environ.get("MITTELO_KIRO_MODEL")
        self.workdir = workdir

    def run_loop(self, poll_interval: float = 1.0):
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
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
        
        logging.info(f"Leased task {task_id}: {prompt[:50]}...")
        
        try:
            result = self._run_kiro(prompt, system_prompt)
            self.client.call("ack", {"task_id": task_id, "status": "done", "result": result})
            logging.info(f"Task {task_id} done.")
        except Exception as e:
            error_msg = str(e)
            self.client.call("ack", {"task_id": task_id, "status": "failed", "error": error_msg})
            logging.error(f"Task {task_id} failed: {error_msg}")

    def _run_kiro(self, prompt: str, system_prompt: str | None = None) -> str:
        cmd = ["kiro-cli", "chat", "--no-interactive", "--wrap", "never"]
        if self.model:
            cmd.extend(["--model", self.model])
            
        # Trust all tools as requested (no sandbox, full access)
        cmd.append("--trust-all-tools")
        
        # Pass prompt as argument (prepend system prompt if present)
        full_prompt = f"System: {system_prompt}\n\nUser: {prompt}" if system_prompt else prompt
        cmd.append(full_prompt)
        
        # Run in current working directory (or specific one if needed, but user said "here")
        # We inherit environment variables to allow login persistence if it uses env vars or home dir
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
            raise RuntimeError(f"kiro-cli failed (code {process.returncode}): {msg}")
            
        return process.stdout or ""
