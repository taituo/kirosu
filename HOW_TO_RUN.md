# How to Run Kirosu

## Prerequisites
- Python 3.10+
- `uv` (recommended) or `pip`
- `kiro-cli` installed and configured (for real execution)

## Installation
```bash
# Install dependencies
uv pip install -e .
```

## Running the Swarm

1. **Start the Hub**
   In a separate terminal:
   ```bash
   uv run kirosu/cli.py hub
   ```

2. **Start the Dashboard (Optional)**
   In another terminal:
   ```bash
   uv run kirosu/cli.py dashboard
   ```

3. **Start an Agent**
   In another terminal (you can run multiple):
   ```bash
   uv run kirosu/cli.py agent
   ```

## Running Demos

### 1. Massive Data Processing
```bash
uv run examples/massive_data.py
```

### 2. Bug Hunter
```bash
uv run examples/bug_hunter.py
```

### 3. Artifact Generation Demo
```bash
uv run examples/artifact_demo.py
```

## Configuration
Global configuration is stored in `~/.kirosu/config.toml`.
Local configuration can be placed in `.kiro/config.toml`.

Example `config.toml`:
```toml
[database]
path = "/path/to/kirosu.db"

[agents.default]
model = "claude-haiku-4.5"
workdir = "/tmp/kirosu_work"
```
