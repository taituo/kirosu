from __future__ import annotations

import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any


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
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_db()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _init_db(self) -> None:
        with self._lock:
            cur = self._db.cursor()
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
            self._db.commit()

    def enqueue(self, prompt: str, system_prompt: str | None = None, task_type: str = "chat") -> int:
        with self._lock:
            now = time.time()
            cur = self._db.cursor()
            cur.execute(
                "INSERT INTO tasks (prompt, system_prompt, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (prompt, system_prompt, task_type, "queued", now, now),
            )
            self._db.commit()
            return cur.lastrowid  # type: ignore

    def lease(self, worker_id: str, max_tasks: int, lease_seconds: int) -> list[Task]:
        now = time.time()
        leased_until = now + float(lease_seconds)
        with self._lock:
            cur = self._db.cursor()
            cur.execute(
                """
                SELECT task_id FROM tasks
                WHERE status = 'queued' OR (status='leased' AND leased_until IS NOT NULL AND leased_until < ?)
                ORDER BY task_id ASC
                LIMIT ?
                """,
                (now, max_tasks),
            )
            ids = [int(r["task_id"]) for r in cur.fetchall()]
            tasks: list[Task] = []
            for task_id in ids:
                cur.execute(
                    """
                    UPDATE tasks
                    SET status='leased', updated_at=?, leased_until=?, worker_id=?
                    WHERE task_id=?
                    """,
                    (now, leased_until, worker_id, task_id),
                )
                cur.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,))
                row = cur.fetchone()
                if row is not None:
                    tasks.append(self._row_to_task(row))
            self._db.commit()
            return tasks

    def ack(self, task_id: int, status: str, result: str | None, error: str | None) -> None:
        now = time.time()
        status_norm = status.lower().strip()
        if status_norm not in {"done", "failed"}:
            raise ValueError("status must be done|failed")
        with self._lock:
            cur = self._db.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status=?, updated_at=?, leased_until=NULL, result=?, error=?
                WHERE task_id=?
                """,
                (status_norm, now, result, error, task_id),
            )
            self._db.commit()

    def approve_task(self, task_id: int, approver: str = "human") -> None:
        now = time.time()
        with self._lock:
            cur = self._db.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status='done', updated_at=?, leased_until=NULL, result=?, worker_id=?
                WHERE task_id=?
                """,
                (now, f"Approved by {approver}", approver, task_id),
            )
            self._db.commit()

    def list(self, status: str | None, limit: int) -> list[Task]:
        with self._lock:
            cur = self._db.cursor()
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

    def stats(self) -> dict[str, int]:
        with self._lock:
            cur = self._db.cursor()
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
            out["completed_last_hour"] = cur.fetchone()[0]
            
            # Rich Metrics: Average Duration
            cur.execute("SELECT AVG(updated_at - created_at) FROM tasks WHERE status='done'")
            avg_dur = cur.fetchone()[0]
            out["avg_completion_time_sec"] = round(avg_dur, 2) if avg_dur else 0.0

            # Rich Metrics: Error Rate
            failed = out["failed"]
            done = out["done"]
            if (done + failed) > 0:
                out["error_rate_percent"] = round((failed / (done + failed)) * 100, 2)
            else:
                out["error_rate_percent"] = 0.0
                
            return out

    def retry_all_failed(self) -> int:
        now = time.time()
        with self._lock:
            cur = self._db.cursor()
            cur.execute(
                """
                UPDATE tasks
                SET status='queued', updated_at=?, leased_until=NULL, worker_id=NULL, result=NULL, error=NULL
                WHERE status='failed'
                """,
                (now,),
            )
            count = cur.rowcount
            self._db.commit()
            return count

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

