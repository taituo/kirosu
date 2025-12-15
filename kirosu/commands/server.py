import argparse
import sys
from ..mcp_server import run_mcp_server
from ..api import run_api

def register(subparsers):
    # MCP command
    subparsers.add_parser("mcp", help="Start the MCP server")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start the REST API")
    api_parser.add_argument("--host", default="127.0.0.1", help="API host")
    api_parser.add_argument("--port", type=int, default=8000, help="API port")

def handle_mcp(args):
    run_mcp_server()
    sys.exit(0)

def handle_api(args):
    run_api(args.host, args.port)
    sys.exit(0)
