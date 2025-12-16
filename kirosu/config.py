import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib
from pathlib import Path
from typing import Any

# Default paths
GLOBAL_CONFIG_DIR = Path.home() / ".kiro"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.toml"
DEFAULT_DB_PATH = GLOBAL_CONFIG_DIR / "kirosu.db"

LOCAL_CONFIG_DIR = Path.cwd() / ".kiro"
LOCAL_CONFIG_FILE = LOCAL_CONFIG_DIR / "config.toml"


# MCP Config paths
GLOBAL_MCP_FILE = GLOBAL_CONFIG_DIR / "settings" / "mcp.json"
LOCAL_MCP_FILE = LOCAL_CONFIG_DIR / "settings" / "mcp.json"

def _merge_dicts(base: dict, update: dict) -> dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for k, v in update.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge_dicts(result[k], v)
        else:
            result[k] = v
    return result

def load_config() -> dict[str, Any]:
    """Load configuration from global and local config files."""
    config = {}
    
    # Load global
    if GLOBAL_CONFIG_FILE.exists():
        try:
            with open(GLOBAL_CONFIG_FILE, "rb") as f:
                config = tomllib.load(f)
        except Exception as e:
            print(f"Warning: Failed to load global config: {e}")
            
    # Load local (overrides global)
    if LOCAL_CONFIG_FILE.exists():
        try:
            with open(LOCAL_CONFIG_FILE, "rb") as f:
                local_config = tomllib.load(f)
                config = _merge_dicts(config, local_config)
        except Exception as e:
            print(f"Warning: Failed to load local config: {e}")
            
    return config

def load_mcp_config() -> dict[str, Any]:
    """Load MCP configuration from global and local mcp.json files."""
    import json
    config = {"mcpServers": {}}
    
    # Load global mcp.json
    if GLOBAL_MCP_FILE.exists():
        try:
            with open(GLOBAL_MCP_FILE, "r") as f:
                global_mcp = json.load(f)
                config = _merge_dicts(config, global_mcp)
        except Exception as e:
            print(f"Warning: Failed to load global MCP config: {e}")

    # Load local mcp.json
    if LOCAL_MCP_FILE.exists():
        try:
            with open(LOCAL_MCP_FILE, "r") as f:
                local_mcp = json.load(f)
                config = _merge_dicts(config, local_mcp)
        except Exception as e:
            print(f"Warning: Failed to load local MCP config: {e}")
            
    return config

def get_db_path() -> str:
    """Get the database path from config or default."""
    config = load_config()
    db_path = config.get("database", {}).get("path")
    if db_path:
        return os.path.expanduser(db_path)
    
    # Ensure directory exists
    GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return str(DEFAULT_DB_PATH)

def get_agent_config(agent_name: str) -> dict[str, Any]:
    """Load specific agent config."""
    config = load_config()
    return config.get("agents", {}).get(agent_name, {})
