import argparse
import sys
from ..strategy import print_strategy_suggestion, print_available_strategies, RecursiveStrategy

def register(subparsers):
    # Suggest command
    suggest_parser = subparsers.add_parser("suggest", help="Suggest agent topology for a task")
    suggest_parser.add_argument("task", nargs="?", help="Description of the task")
    suggest_parser.add_argument("--list", action="store_true", help="List available strategies")

    # Recursive run command
    recursive_parser = subparsers.add_parser("run-recursive", help="Auto-plan and execute a task")
    recursive_parser.add_argument("task", help="The high-level task to plan and execute")

def handle_suggest(args):
    if args.list:
        print_available_strategies()
    elif args.task:
        print_strategy_suggestion(args.task)
    else:
        print("Error: Please provide a task description or use --list.")
        sys.exit(1)
    sys.exit(0)

def handle_recursive(args):
    RecursiveStrategy.execute(args.task)
    sys.exit(0)
