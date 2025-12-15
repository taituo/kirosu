import argparse
import sys
from typing import NoReturn
from .commands import hub, agent, task, ui, server, strategy

def main() -> NoReturn:
    parser = argparse.ArgumentParser(description="Kiro Swarm Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Register all commands
    hub.register(subparsers)
    agent.register(subparsers)
    task.register(subparsers)
    ui.register(subparsers)
    server.register(subparsers)
    strategy.register(subparsers)

    args = parser.parse_args()

    # Dispatch to handlers
    if args.command == "hub":
        hub.handle(args)
    elif args.command == "agent":
        agent.handle(args)
    elif args.command == "enqueue":
        task.handle_enqueue(args)
    elif args.command == "status":
        task.handle_status(args)
    elif args.command == "approve":
        task.handle_approve(args)
    elif args.command == "dashboard":
        ui.handle(args)
    elif args.command == "mcp":
        server.handle_mcp(args)
    elif args.command == "api":
        server.handle_api(args)
    elif args.command == "suggest":
        strategy.handle_suggest(args)
    elif args.command == "run-recursive":
        strategy.handle_recursive(args)

if __name__ == "__main__":
    main()
