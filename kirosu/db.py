from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any
from queue import Queue


@dataclass(frozen=True)
class Task:
    task_id: int
    prompt: str
    system_prompt: str | None
    type: str  # "chat" or "python"
    status: str
    created_at: float
    updated_at: float
    leased_until: float | None
    worker_id: str | None
    result: str | None
    error: str | None


class TaskStore:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self._pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._pool.put(conn)
        self._init_db()

    def close(self) -> None:
        while not self._pool.empty():
            conn = self._pool.get()
            conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        """Get connection from pool (blocking if empty)."""
        return self._pool.get()

    def _return_conn(self, conn: sqlite3.Connection) -> None:
        """Return connection to pool."""
        self._pool.put(conn)

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA synchronous=NORMAL;")
            cur.execute("PRAGMA busy_timeout=3000;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                  task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  prompt TEXT NOT NULL,
                  system_prompt TEXT,
                  type TEXT DEFAULT 'chat',
                  status TEXT NOT NULL,
                  created_at REAL NOT NULL,
                  updated_at REAL NOT NULL,
                  leased_until REAL,
                  worker_id TEXT,
                  result TEXT,
                  error TEXT
                )
                """
            )
            # P0 Optimization: Add composite index for lease() query performance
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_lease_status_leased_until
                ON tasks(status, leased_until)
                """
            )
            conn.commit()
        finally:
            self._return_conn(conn)

    def enqueue(self, prompt: str, system_prompt: str | None = None, task_type: str = "chat") -> int:
        conn = self._get_conn()
        try:
            now = time.time()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (prompt, system_prompt, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (prompt, system_prompt, task_type, "queued", now, now),
            )
            conn.commit()
            return cur.lastrowid  # type: ignore
        finally:
            self._return_conn(conn)

    def lease(self, worker_id: str, max_tasks: int, lease_seconds: int) -> list[Task]:
        """
        Optimized lease method using atomic UPDATE...RETURNING (P0) 
        and connection pooling (P1) to eliminate global lock contention.
        """
        conn = self._get_conn()
        try:
            now = time.time()
            leased_until = now + float(lease_seconds)
            cur = conn.cursor()
            
            # P0 Optimization: Single atomic UPDATE...RETURNING
            # Replaces N+1 query pattern (Select + N Updates + N Selects)
            cur.execute(
                """
                UPDATE tasks
                SET status='leased', updated_at=?, leased_until=?, worker_id=?
                WHERE task_id IN (
                    SELECT task_id FROM tasks
                    WHERE status = 'queued' OR (status='leased' AND leased_until IS NOT NULL AND leased_until < ?)
                    ORDER BY task_id ASC
                    LIMIT ?
                )
                RETURNING *
                """,
                (now, leased_until, worker_id, now, max_tasks),
            )
            
            tasks = [self._row_to_task(r) for r in cur.fetchall()]
            conn.commit()
            return tasks
        finally:
            self._return_conn(conn)

    def ack(self, task_id: int, status: str, result: str | None, error: str | None) -> None:
        conn = self._get_conn()
        try:
            now = time.time()
            status_norm = status.lower().strip()
            if status_norm not in {"done", "failed"}:
                raise ValueError("status must be done|failed")
                
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status=?, updated_at=?, leased_until=NULL, result=?, error=?
                WHERE task_id=?
                """,
                (status_norm, now, result, error, task_id),
            )
            conn.commit()
        finally:
            self._return_conn(conn)

    def approve_task(self, task_id: int, approver: str = "human") -> None:
        conn = self._get_conn()
        try:
            now = time.time()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status='done', updated_at=?, leased_until=NULL, result=?, worker_id=?
                WHERE task_id=?
                """,
                (now, f"Approved by {approver}", approver, task_id),
            )
            conn.commit()
        finally:
            self._return_conn(conn)

    def list(self, status: str | None, limit: int) -> list[Task]:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            status_norm = status.lower().strip() if status else None

            if limit <= 0:
                if status_norm:
                    cur.execute("SELECT * FROM tasks WHERE status=? ORDER BY task_id DESC", (status_norm,))
                else:
                    cur.execute("SELECT * FROM tasks ORDER BY task_id DESC")
            else:
                if status_norm:
                    cur.execute(
                        "SELECT * FROM tasks WHERE status=? ORDER BY task_id DESC LIMIT ?",
                        (status_norm, limit),
                    )
                else:
                    cur.execute("SELECT * FROM tasks ORDER BY task_id DESC LIMIT ?", (limit,))

            return [self._row_to_task(r) for r in cur.fetchall()]
        finally:
            self._return_conn(conn)

    def stats(self) -> dict[str, int]:
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT status, COUNT(*) AS n FROM tasks GROUP BY status")
            out: dict[str, Any] = {"queued": 0, "leased": 0, "done": 0, "failed": 0}
            total = 0
            for r in cur.fetchall():
                c = int(r["n"])
                out[str(r["status"])] = c
                total += c
            out["total_tasks"] = total
            
            # Rich Metrics: Completion Rate (Last 1 hour)
            one_hour_ago = time.time() - 3600
            cur.execute("SELECT COUNT(*) FROM tasks WHERE status='done' AND updated_at > ?", (one_hour_ago,))
            res_count = cur.fetchone()
            out["completed_last_hour"] = res_count[0] if res_count else 0
            
            # Rich Metrics: Average Duration
            cur.execute("SELECT AVG(updated_at - created_at) FROM tasks WHERE status='done'")
            res_avg = cur.fetchone()
            avg_dur = res_avg[0] if res_avg else None
            out["avg_completion_time_sec"] = round(avg_dur, 2) if avg_dur else 0.0

            # Rich Metrics: Error Rate
            failed = out["failed"]
            done = out["done"]
            if (done + failed) > 0:
                out["error_rate_percent"] = round((failed / (done + failed)) * 100, 2)
            else:
                out["error_rate_percent"] = 0.0
                
            return out
        finally:
            self._return_conn(conn)

    def retry_all_failed(self) -> int:
        conn = self._get_conn()
        try:
            now = time.time()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status='queued', updated_at=?, leased_until=NULL, worker_id=NULL, result=NULL, error=NULL
                WHERE status='failed'
                """,
                (now,),
            )
            count = cur.rowcount
            conn.commit()
            return count
        finally:
            self._return_conn(conn)

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Task:
        return Task(
            task_id=int(row["task_id"]),
            prompt=str(row["prompt"]),
            system_prompt=row["system_prompt"],
            type=row["type"] if "type" in row.keys() else "chat",
            status=str(row["status"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            leased_until=float(row["leased_until"]) if row["leased_until"] is not None else None,
            worker_id=str(row["worker_id"]) if row["worker_id"] is not None else None,
            result=str(row["result"]) if row["result"] is not None else None,
            error=str(row["error"]) if row["error"] is not None else None,
        )

