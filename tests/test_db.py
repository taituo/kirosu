import pytest
import time
from kiro_swarm.db import TaskStore

def test_enqueue(store):
    task_id = store.enqueue("test prompt", system_prompt="sys prompt")
    assert task_id > 0
    
    tasks = store.list(status="queued", limit=10)
    assert len(tasks) == 1
    assert tasks[0].prompt == "test prompt"
    assert tasks[0].system_prompt == "sys prompt"
    assert tasks[0].status == "queued"

def test_lease(store):
    store.enqueue("task 1")
    store.enqueue("task 2")
    
    tasks = store.lease("worker1", max_tasks=1, lease_seconds=10)
    assert len(tasks) == 1
    assert tasks[0].prompt == "task 1"
    assert tasks[0].worker_id == "worker1"
    assert tasks[0].status == "leased"
    
    # Lease again, should get task 2
    tasks2 = store.lease("worker1", max_tasks=1, lease_seconds=10)
    assert len(tasks2) == 1
    assert tasks2[0].prompt == "task 2"

def test_ack(store):
    tid = store.enqueue("task")
    store.lease("worker1", 1, 10)
    
    store.ack(tid, "done", result="ok", error=None)
    
    tasks = store.list(status="done", limit=1)
    assert len(tasks) == 1
    assert tasks[0].result == "ok"
    assert tasks[0].status == "done"

def test_retry_failed(store):
    tid = store.enqueue("fail task")
    store.lease("w1", 1, 10)
    store.ack(tid, "failed", result=None, error="oops")
    
    count = store.retry_all_failed()
    assert count == 1
    
    tasks = store.list(status="queued", limit=1)
    assert len(tasks) == 1
    assert tasks[0].prompt == "fail task"
