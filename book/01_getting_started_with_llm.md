# 01. Getting Started with LLM CLIs

> "The true power of Large Language Models is unlocked when they become composable parts of your terminal workflow, not just chatbots in a browser tab."

## Why CLI?

If you are accustomed to using ChatGPT or Claude via a web interface, you might wonder why tools like `kirosu`, `codex`, or `kiro-cli` leverage the command line.

### 1. Composability (The Unix Philosophy)
In a CLI, the output of one tool can be the input of another.
- **Web**: *Copy* log error -> *Switch* tab -> *Paste* to ChatGPT -> *Wait* -> *Copy* solution -> *Switch* tab -> *Paste* to IDE.
- **CLI**: `cat server.log | codex "Fix the error in this log" > solution.py`

### 2. Context Management
Web UIs are isolated from your filesystem. CLIs live *in* your filesystem.
- Kirosu can "see" your project structure.
- You can pipe file contents directly: `codex -i src/main.py "Refactor this"`

### 3. Automation & Scripting
You cannot put a web browser session into a cron job. You *can* put a CLI command into a script.
Kirosu takes this to the extreme by allowing you to script *swarms* of agents.

## Recommended Tools

To get the most out of Kirosu, you should be comfortable with at least one LLM CLI tool:

### 1. Codex CLI (Recommended for Frontier Models)
The official, high-performance CLI for advanced models.
- **Usage**: `codex "hello"`
- **Kirosu Integration**: Native (`KIRO_PROVIDER=codex`).
- **Best For**: Heavy lifting, autonomous agents, code generation.

### 2. Kiro CLI (Standard)
Our own lightweight wrapper.
- **Usage**: `kiro-cli chat "hello"`
- **Kirosu Integration**: Default.
- **Best For**: Testing, debugging, local models.

### 3. LLM (by Simon Willison)
A popular open-source tool.
- **Usage**: `llm "hello"`
- **Best For**: Experimentation, plugin ecosystem.

## How Kirosu Fits In

Kirosu is an **Orchestrator**.

- A single CLI tool (`codex`) is like a **single Developer**.
- **Kirosu** is like a **PROJECT MANAGER** that directs a team of Developers.

Kirosu uses these CLI tools under the hood to perform the actual work (the "thinking"), but adds the layer of state management (Hub), task queuing, and coordination.

## Next Steps
Now that you understand the "Why", proceed to [running your first swarm](../README.md#quick-start-local).
