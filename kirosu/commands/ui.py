import argparse
import sys
from ..dashboard import run_dashboard

def register(subparsers):
    dash_parser = subparsers.add_parser("dashboard", help="Start the swarm dashboard")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    dash_parser.add_argument("--port", type=int, default=8765, help="Hub port")

def handle(args):
    run_dashboard(args.host, args.port)
    sys.exit(0)
