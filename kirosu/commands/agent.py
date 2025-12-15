import argparse
import sys
from ..agent import KiroAgent

def register(subparsers):
    agent_parser = subparsers.add_parser("agent", help="Start a kiro agent")
    agent_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    agent_parser.add_argument("--port", type=int, default=8765, help="Hub port")
    agent_parser.add_argument("--model", help="Override Kiro model")
    agent_parser.add_argument("--log-file", help="Path to log file")
    agent_parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

def handle(args):
    agent = KiroAgent(args.host, args.port, args.model)
    try:
        agent.run_loop(log_file=args.log_file, verbose=args.verbose)
    except KeyboardInterrupt:
        print("Agent stopped.")
    sys.exit(0)
