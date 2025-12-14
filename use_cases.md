# Kirosu Advanced Use Cases

## 1. Massive Data Processing (1000+ Documents)
**Objective**: Process a large corpus of documents (e.g., summarization, extraction) using a swarm of agents.

**Workdir Strategy**: **Shared**. All agents mount the same `/data` volume or access the same S3 bucket.
```toml
[agents.worker]
workdir = "/mnt/shared_data"
```

## 2. Bug Hunting Swarm
**Objective**: Automatically find bugs in a codebase.

**Workdir Strategy**: **Isolated**. Each agent clones the repo into a private sandbox to avoid race conditions during testing/patching.
```toml
[agents.hunter]
workdir = "/tmp/sandbox/${AGENT_ID}"
```

## 3. Dead Code Hunting
**Objective**: Identify and remove unused code.

**Workdir Strategy**: **Shared (Read-Only)** or **Isolated (Read-Write)**.
- Analysis: Shared repo root.
- Pruning: Isolated branch/worktree per agent.

## 4. Continuous Testing
**Objective**: Run tests continuously on new commits.

**Workdir Strategy**: **Ephemeral**. CI pipeline creates a fresh directory for each run.
