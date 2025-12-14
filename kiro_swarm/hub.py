from __future__ import annotations

import json
import logging
import socketserver
import threading
import time
from dataclasses import asdict
from typing import Any

from .db import TaskStore


class _HubState:
    def __init__(self, store: TaskStore, lease_seconds: int):
        self.store = store
        self.lease_seconds = lease_seconds
        self._shutdown = threading.Event()

    def shutdown_requested(self) -> bool:
        return self._shutdown.is_set()

    def request_shutdown(self) -> None:
        self._shutdown.set()


class JsonlHubHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        state: _HubState = self.server.state  # type: ignore[attr-defined]
        while not state.shutdown_requested():
            try:
                line = self.rfile.readline()
                if not line:
                    return
                line = line.strip()
                if not line:
                    continue

                req_id = None
                try:
                    req = json.loads(line.decode("utf-8"))
                    req_id = req.get("id")
                    method = req["method"]
                    params = req.get("params") or {}
                    result = self._dispatch(state, method, params)
                    resp = {"id": req_id, "result": result, "error": None}
                except Exception as e:
                    resp = {"id": req_id, "result": None, "error": {"message": str(e)}}

                self.wfile.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()
            except (ConnectionResetError, BrokenPipeError):
                return

    def _dispatch(self, state: _HubState, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "enqueue":
            prompt = str(params["prompt"])
            system_prompt = params.get("system_prompt")
            task_id = state.store.enqueue(prompt, system_prompt=str(system_prompt) if system_prompt else None)
            return {"task_id": task_id}

        if method == "lease":
            worker_id = str(params.get("worker_id") or "worker")
            max_tasks = int(params.get("max_tasks") or 1)
            lease_seconds = int(params.get("lease_seconds") or state.lease_seconds)
            tasks = state.store.lease(worker_id=worker_id, max_tasks=max_tasks, lease_seconds=lease_seconds)
            return {"tasks": [asdict(t) for t in tasks]}

        if method == "ack":
            task_id = int(params["task_id"])
            status = str(params["status"])
            result = params.get("result")
            error = params.get("error")
            state.store.ack(task_id=task_id, status=status, result=result, error=error)
            return {"ok": True}

        if method == "list":
            status = params.get("status")
            limit_param = params.get("limit")
            limit = int(limit_param) if limit_param is not None else 50
            tasks = state.store.list(status=status, limit=limit)
            return {"tasks": [asdict(t) for t in tasks], "stats": state.store.stats()}

        if method == "stats":
            return {"stats": state.store.stats()}

        if method == "retry_failed":
            count = state.store.retry_all_failed()
            return {"retried": count}

        if method == "shutdown":
            state.request_shutdown()
            return {"ok": True}

        raise ValueError(f"Unknown method: {method}")


class ThreadedTcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_hub(
    db_path: str,
    host: str,
    port: int,
    lease_seconds: int,
    ready_callback: Any | None = None,
) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    store = TaskStore(db_path)
    state = _HubState(store, lease_seconds=lease_seconds)

    with ThreadedTcpServer((host, port), JsonlHubHandler) as srv:
        srv.state = state  # type: ignore[attr-defined]
        actual_host, actual_port = srv.server_address
        logging.info(f"KIRO_SWARM_HUB tcp://{actual_host}:{actual_port}")
        
        if ready_callback:
            ready_callback(actual_port)


        try:
            while not state.shutdown_requested():
                srv.handle_request()
        finally:
            try:
                store.close()
            except Exception:
                pass
    time.sleep(0.05)
    return actual_port

