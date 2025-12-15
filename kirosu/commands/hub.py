import argparse
import sys
from ..hub import run_hub
from ..config import get_db_path

def register(subparsers):
    hub_parser = subparsers.add_parser("hub", help="Start the swarm hub")
    hub_parser.add_argument("--host", default="127.0.0.1", help="Hub host")
    hub_parser.add_argument("--port", type=int, default=8765, help="Hub port")
    hub_parser.add_argument("--db", default=get_db_path(), help="Database path")
    hub_parser.add_argument("--lease-seconds", type=int, default=300, help="Task lease duration")

def handle(args):
    sys.exit(run_hub(args.db, args.host, args.port, args.lease_seconds))
