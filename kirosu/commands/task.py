import argparse
import sys
from ..agent import HubClient

def register(subparsers):
    # Enqueue command
    enqueue_parser = subparsers.add_parser("enqueue", help="Enqueue a task")
    enqueue_parser.add_argument("prompt", help="The prompt to execute")
    enqueue_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    enqueue_parser.add_argument("--port", type=int, default=8765, help="Hub port")

    # Status command
    status_parser = subparsers.add_parser("status", help="List tasks")
    status_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    status_parser.add_argument("--port", type=int, default=8765, help="Hub port")
    status_parser.add_argument("--limit", type=int, default=50, help="Limit results")
    status_parser.add_argument("--status", help="Filter by status")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve a human-in-the-loop task")
    approve_parser.add_argument("task_id", type=int, help="ID of the task to approve")

def handle_enqueue(args):
    client = HubClient(args.host, args.port)
    resp = client.call("enqueue", {"prompt": args.prompt})
    print(f"Task enqueued. ID: {resp['task_id']}")
    sys.exit(0)

def handle_status(args):
    client = HubClient(args.host, args.port)
    resp = client.call("list", {"limit": args.limit, "status": args.status})
    tasks = resp.get("tasks", [])
    stats = resp.get("stats", {})
    
    print(f"Stats: {stats}")
    print("-" * 60)
    print(f"{'ID':<5} | {'Status':<10} | {'Prompt':<40}")
    print("-" * 60)
    for t in tasks:
        prompt = t['prompt'].replace('\n', ' ')
        if len(prompt) > 37:
            prompt = prompt[:37] + "..."
        print(f"{t['task_id']:<5} | {t['status']:<10} | {prompt:<40}")
        if t['result']:
            print(f"  Result: {t['result'][:100]}...")
        if t['error']:
            print(f"  Error: {t['error']}")
    sys.exit(0)

def handle_approve(args):
    client = HubClient(args.host, args.port)
    resp = client.call("approve", {"task_id": args.task_id})
    print(f"Task {args.task_id} approved.")
    sys.exit(0)
