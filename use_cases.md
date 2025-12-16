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

## 5. Feature Development Swarm
**Objective**: End-to-end feature implementation using specialized agents.

**Topology**: Recursive / Parallel
1.  **Requirements Agent**: Analyzes specs and creates a checklist.
2.  **Architecture Agent**: Designs the components and API.
3.  **Coder Agent**: Implements the feature and tests.
4.  **QA Agent**: Reviews code and security.

**Snippet**:
```python
# Pseudo-code for a Feature Swarm
swarm.run([
    {"role": "Architect", "task": "Design schema for OAuth2"},
    {"role": "Backend", "task": "Implement API endpoints"},
    {"role": "Frontend", "task": "Create Login UI"},
    {"role": "QA", "task": "Verify security"}
])
```

## 6. The "Context Sieve" Pattern (Data Filter)

**Problem:** Some MCP tools (e.g., database dumps, log analyzers, detailed API responses) return massive amounts of JSON/text, instantly filling the context window and confusing the LLM.

**Solution:**
Delegate the heavy tool usage to a specialized "Sieve Agent".
1.  **Main Agent**: "I need to know the error rate from yesterday's logs. Ask the LogAnalyzer agent."
2.  **Sieve Agent**: Calls the noisy `fetch_logs` tool (receiving 10MB of text).
3.  **Sieve Agent**: Analyzes the raw data internally.
4.  **Sieve Agent**: Returns *only* the answer: "The error rate was 0.5% with 23 exceptions."
5.  **Main Agent**: Receives clean, concise data. Context remains empty of noise.

**Ideal for:**
-   Log analysis
-   Database schema exploration
-   Large API responses (e.g., list of 1000 repositories)
-   File system crawling

## 7. Automated Code Review
**Objective**: Instant feedback on Pull Requests.

**Topology**: Parallel Swarm
- **Security Reviewer**: Checks for injection flaws, auth bypass.
- **Performance Analyst**: Checks for N+1 queries, memory leaks.
- **Style Enforcer**: Checks PEP8/Linting.
- **Test Validator**: Ensures coverage > 80%.

## 7. Frontier Model Swarm (Codex)
**Objective**: Utilize next-generation models for extremely complex or rapid autonomous coding.

**Configuration**:
- **Provider**: `CodexProvider`
- **Model**: `gpt-5.1-codex-mini` (or `gpt-6-preview` if available)
- **Flags**: `--dangerously-bypass-approvals-and-sandbox` (Requires isolated environment)

**Setup**:
```bash
# High-speed autonomous mode
export KIRO_PROVIDER=codex
kirosu agent --model gpt-5.1-codex-mini
```
This mode bypasses all user confirmation steps, allowing for true autonomous operation at the speed of the API. Ideal for overnight batch processing or massive refactoring jobs.
