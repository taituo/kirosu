# Kirosu Advanced Use Cases

## 1. Massive Data Processing (1000+ Documents)
**Objective**: Process a large corpus of documents (e.g., summarization, extraction) using a swarm of agents.

**Architecture**:
- **Splitter Agent**: Reads the directory, chunks documents, and enqueues tasks.
- **Worker Swarm**: 5-50 agents running in parallel (via `kirosu agent`).
- **Aggregator Agent**: Monitors for completion and combines results.

**Configuration**:
```toml
# ~/.kirosu/config.toml
[database]
path = "/data/kirosu_massive.db"

[agents.worker]
model = "gemini-1.5-flash"
workdir = "/tmp/kirosu_workers"
```

## 2. Bug Hunting Swarm
**Objective**: Automatically find bugs in a codebase.

**Workflow**:
1.  **Scanner**: Enqueues tasks for each file to analyze static analysis results.
2.  **Reproducer**: "Thinker" agent (Generator) writes a reproduction script for potential bugs.
3.  **Verifier**: "Thinker" agent (Judge) runs the script to confirm the bug.
4.  **Fixer**: If verified, generates a patch.

## 3. Dead Code Hunting
**Objective**: Identify and remove unused code.

**Workflow**:
1.  **Indexer**: Maps all symbols and references.
2.  **Analyzer**: Identifies symbols with zero references.
3.  **Pruner**: Creates a PR to remove dead code (requires "Dangerous" Python execution).

## 4. Continuous Testing
**Objective**: Run tests continuously on new commits.

**Integration**:
- Use `kirosu mcp` to integrate with CI/CD pipelines.
- Trigger swarm on every push to run a suite of "Tester" agents.
