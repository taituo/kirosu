# 👨‍💻 Developer Cookbook: Kirosu as a Library

Kirosu isn't just a CLI tool -- it's a **Python Framework** for building agentic systems.

While `kiro-cli` is great for quick chats, serious applications (like Betting Bots, CI/CD Pipelines, or Swarms) are built by writing **Python Code**.

## The "Orchestrator" Pattern

Instead of config files (`.yaml`), you write a driver script (`main.py`) that acts as the God-Module.

### 1. Import the Client
We utilize the `SwarmClient` to talk to the Hub programmatically.

```python
import asyncio
from kirosu.client import SwarmClient

async def main():
    async with SwarmClient(port=8765) as client:
        # Your logic here
        pass
```

### 2. Spawning Agents (Process Management)
You can start the Hub and Agents directly from Python using `subprocess`. This keeps your entire system self-contained in one script.

```python
import sys
import subprocess

# Start Hub
hub = subprocess.Popen([sys.executable, "-m", "kirosu.cli", "hub"])

# Start Worker
worker = subprocess.Popen([
    sys.executable, "-m", "kirosu.cli", "agent", 
    "--id", "worker_1", 
    "--model", "gpt-5.1-codex-mini"
])
```

### 3. Defining Workflows (The Logic)
Now you can write complex logic using Python's full power (`if`, `for`, `while`, database calls, APIs).

**Example: The "Review Chain"**
```python
task_id = await client.add_task("Write code for X")
result = await wait_for_result(client, task_id)

if "error" in result:
    await client.add_task(f"Fix this error: {result}")
else:
    await client.add_task(f"Review this code: {result}")
```

## Why Code > Config?

1.  **Debugging**: You can use `pdb` or print statements to debug your orchestration logic.
2.  **Dynamic Topology**: You can spawn new agents *based on data*. (e.g., "If load > 90%, spawn 5 more workers").
3.  **Integration**: You can connect directly to your existing SQL databases, Redis, or Flask apps.

## Key Files to Study
*   `examples/verified_chain_demo.py`: Shows sequential orchestration.
*   `examples/live_odds_monitor.py`: Shows real-time looping and signaling.
*   `kirosu/client.py`: The wrapper for the API protocols.
