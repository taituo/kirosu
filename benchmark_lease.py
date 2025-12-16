#!/usr/bin/env python3
"""
Performance benchmark for TaskStore.lease() method.
Measures current implementation vs. optimized versions.
"""

import sqlite3
import tempfile
import time
import threading
from pathlib import Path
from kirosu.db import TaskStore


def setup_test_db(num_tasks: int = 10000) -> tuple[str, TaskStore]:
    """Create test database with N queued tasks."""
    db_path = tempfile.mktemp(suffix=".db")
    store = TaskStore(db_path)

    # Bulk insert tasks
    now = time.time()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    tasks = [(f"prompt_{i}", None, "chat", "queued", now, now)
             for i in range(num_tasks)]
    cur.executemany(
        "INSERT INTO tasks (prompt, system_prompt, type, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        tasks
    )
    conn.commit()
    conn.close()

    return db_path, store


def benchmark_current_lease(store: TaskStore, iterations: int = 100, max_tasks: int = 100):
    """Benchmark current lease() implementation."""
    times = []

    for i in range(iterations):
        start = time.perf_counter()
        tasks = store.lease(f"worker_{i % 10}", max_tasks, 30)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # Convert to ms

    return times


def benchmark_concurrent_lease(store: TaskStore, num_workers: int = 10, iterations: int = 50):
    """Benchmark lease() under concurrent load."""
    times = [[] for _ in range(num_workers)]

    def worker_thread(worker_id: int):
        for i in range(iterations):
            start = time.perf_counter()
            tasks = store.lease(f"worker_{worker_id}", 100, 30)
            elapsed = time.perf_counter() - start
            times[worker_id].append(elapsed * 1000)

    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(num_workers)]

    start_total = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total_time = time.perf_counter() - start_total

    all_times = [t for worker_times in times for t in worker_times]
    return all_times, total_time


def analyze_times(times: list[float], label: str):
    """Compute statistics on timing data."""
    if not times:
        return

    times_sorted = sorted(times)
    n = len(times_sorted)

    print(f"\n{label}")
    print(f"  Calls: {n}")
    print(f"  Min: {times_sorted[0]:.2f}ms")
    print(f"  Max: {times_sorted[-1]:.2f}ms")
    print(f"  Mean: {sum(times) / n:.2f}ms")
    print(f"  Median: {times_sorted[n // 2]:.2f}ms")
    print(f"  P99: {times_sorted[int(n * 0.99)]:.2f}ms")
    print(f"  P95: {times_sorted[int(n * 0.95)]:.2f}ms")
    print(f"  Throughput: {1000 / (sum(times) / n):.1f} calls/sec")


def main():
    print("=" * 70)
    print("TaskStore.lease() Performance Benchmark")
    print("=" * 70)

    # Test 1: Sequential baseline
    print("\n[Test 1] Sequential Baseline (1K tasks, 100 iterations)")
    db_path, store = setup_test_db(1000)
    try:
        times = benchmark_current_lease(store, iterations=100, max_tasks=10)
        analyze_times(times, "Sequential lease() calls")
    finally:
        store.close()
        if Path(db_path).exists():
            Path(db_path).unlink()

    # Test 2: Larger dataset
    print("\n[Test 2] Larger Dataset (10K tasks, 50 iterations)")
    db_path, store = setup_test_db(10000)
    try:
        times = benchmark_current_lease(store, iterations=50, max_tasks=100)
        analyze_times(times, "lease() with 10K tasks")
    finally:
        store.close()
        if Path(db_path).exists():
            Path(db_path).unlink()

    # Test 3: Concurrent load
    print("\n[Test 3] Concurrent Load (10K tasks, 10 workers, 50 iterations each)")
    db_path, store = setup_test_db(10000)
    try:
        times, total_time = benchmark_concurrent_lease(store, num_workers=10, iterations=50)
        analyze_times(times, "Concurrent lease() calls")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Effective throughput: {len(times) / total_time:.1f} calls/sec")
    finally:
        store.close()
        if Path(db_path).exists():
            Path(db_path).unlink()

    # Test 4: High contention scenario
    print("\n[Test 4] High Contention (100K tasks, 20 workers, 25 iterations each)")
    db_path, store = setup_test_db(100000)
    try:
        times, total_time = benchmark_concurrent_lease(store, num_workers=20, iterations=25)
        analyze_times(times, "High contention lease() calls")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Effective throughput: {len(times) / total_time:.1f} calls/sec")
    finally:
        store.close()
        if Path(db_path).exists():
            Path(db_path).unlink()

    print("\n" + "=" * 70)
    print("Benchmark Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
