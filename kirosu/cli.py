import argparse
import sys
import time
from typing import NoReturn

from .hub import run_hub
from .agent import KiroAgent, HubClient
from .dashboard import run_dashboard
from .mcp_server import run_mcp_server
from .api import run_api
from .config import get_db_path


def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="Kiro Swarm Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Hub command
    hub_parser = subparsers.add_parser("hub", help="Start the swarm hub")
    hub_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    hub_parser.add_argument("--port", type=int, default=8765, help="Hub port")
    hub_parser.add_argument("--db", default=get_db_path(), help="Database path")
    hub_parser.add_argument("--lease-seconds", type=int, default=300, help="Task lease duration")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Start a kiro agent")
    agent_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    agent_parser.add_argument("--port", type=int, default=8765, help="Hub port")
    agent_parser.add_argument("--model", help="Override Kiro model")

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

    # Dashboard command
    dash_parser = subparsers.add_parser("dashboard", help="Start the swarm dashboard")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    dash_parser.add_argument("--port", type=int, default=8765, help="Hub port")

    # MCP command
    subparsers.add_parser("mcp", help="Start the MCP server")

    # API command
    api_parser = subparsers.add_parser("api", help="Start the REST API")
    api_parser.add_argument("--host", default="127.0.0.1", help="API host")
    api_parser.add_argument("--port", type=int, default=8000, help="API port")

    args = parser.parse_args()

    if args.command == "hub":
        sys.exit(run_hub(args.db, args.host, args.port, args.lease_seconds))

    elif args.command == "agent":
        agent = KiroAgent(args.host, args.port, args.model)
        try:
            agent.run_loop()
        except KeyboardInterrupt:
            print("Agent stopped.")
        sys.exit(0)

    elif args.command == "enqueue":
        client = HubClient(args.host, args.port)
        resp = client.call("enqueue", {"prompt": args.prompt})
        print(f"Task enqueued. ID: {resp['task_id']}")
        sys.exit(0)

    elif args.command == "status":
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

    elif args.command == "dashboard":
        run_dashboard(args.host, args.port)
        sys.exit(0)

    elif args.command == "mcp":
        run_mcp_server()
        sys.exit(0)

    elif args.command == "api":
        run_api(args.host, args.port)
        sys.exit(0)

if __name__ == "__main__":
    main()
