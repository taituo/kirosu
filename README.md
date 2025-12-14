# ![Kirosu Logo](kirosu.png) Kirosu 🐝

**Enterprise-grade AI Agent Swarm Orchestrator.**

Kirosu (formerly `kiro-swarm`) is a robust platform for managing swarms of AI agents. It provides a centralized Hub for task management, distributed Agents for execution, and enterprise features like secure authentication and persistent connections.

## 📚 Documentation

- **[Getting Started](HOW_TO_RUN.md)**: Installation and running your first swarm.
- **[Technology & Architecture](technology.md)**: Deep dive into system design and protocols.
- **[Advanced Use Cases](use_cases.md)**: Massive data processing, bug hunting, and more.
- **[Go Support](go/README.md)**: Protocol documentation for Go workers.
- **[User Stories](user_stories.md)**: Original requirements and user flows.

## ✨ Key Features

- **Hub-Agent Architecture**: Centralized SQLite-backed task queue with distributed, stateless workers.
- **Enterprise Grade**:
    - **Security**: Token-based authentication (`KIRO_SWARM_KEY`).
    - **Reliability**: Persistent TCP connections with retry logic.
    - **Flexibility**: "Dangerous" mode for arbitrary Python code execution.
- **Observability**:
    - Real-time TUI Dashboard (`kirosu dashboard`).
    - Structured logging.
- **Integration**:
    - **MCP Server**: Expose swarm capabilities to other AI assistants.
    - **REST API**: FastAPI-based endpoints for programmatic access.
- **Configuration**: Global (`~/.kirosu/`) and local (`.kiro/`) configuration merging.

## 🚀 Demos

We provide ready-to-run examples to demonstrate Kirosu's capabilities:

1.  **[Artifact Generation](examples/artifact_demo.py)**: Single agent creating files.
2.  **[10-Worker Swarm](examples/swarm_demo.py)**: Stress test with 10 concurrent agents.
3.  **[Massive Data Processing](examples/massive_data.py)**: Batch processing pattern.
4.  **[Bug Hunter](examples/bug_hunter.py)**: Automated debugging workflow.

Run them with `uv run examples/<script_name>.py`.

## 🛠️ Development

### Installation
```bash
uv pip install -e .
```

### Running Tests
Kirosu uses `pytest` with mocking to ensure tests are fast and free (no API credits used).
```bash
uv run pytest
```

### Project Structure
- `kirosu/`: Main package source.
    - `hub.py`: Central task server.
    - `agent.py`: Worker implementation.
    - `cli.py`: Command-line interface.
- `examples/`: Demo scripts.
- `tests/`: Comprehensive test suite.
