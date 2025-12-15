# 🧠 Kirosu Memory Architecture (Refined Idea)

This document outlines the vision for **Native Context Management** in Kirosu. This is NOT about complex external vector DBs (though they can exist), but about **explicit, file-based control** over what the agent remembers.

## 1. The Core Concept: "Save Game" for AI
The user (or another agent) explicitly decides when to dump the current mental state to a file, and when to inject it back.

### The "Clone & Resume" Workflow
This solves the "Drunk at a Bar" problem: Agent A rambles, you save the good parts, and Agent B starts fresh with *only* that summary.

1.  **Interact**: You chat with Agent A (Context grows large).
2.  **Save**: You run `/context save ./memories/chapter1.md`.
    *   Kirosu dumps the conversation history (or a summary of it) to a standard Markdown file.
3.  **Reset/Switch**: You start a new Agent B (fresh brain).
4.  **Load**: You run `/context load ./memories/chapter1.md`.
    *   Kirosu injects the content of that file into Agent B's system prompt.
    *   Agent B now "knows" everything Agent A did, but has zero token bloat.

### Why this beats "Auto-Memory"
*   **Precision**: You don't hope the vector DB finds the right chunk. You *give* the agent the exact file.
*   **Portability**: The memory is just a `.md` file. You can git commit it, email it, or edit it manually.
*   **Interoperability**: Since it's Markdown, *any* LLM (Claude, ChatGPT, Kirosu) can read it. It's not locked in a proprietary database.

---

## 2. Advanced Memory Patterns

### A. Semantic Search (Vector Memory)
*   Instead of loading a whole file, the Agent queries a database: `memory.query("What did we agree on last Tuesday?")`.
*   **Tech**: SQLite `vec` extension or `ChromaDB`.
*   **Workflow**:
    1.  User sends prompt.
    2.  System embeds prompt -> finds top-5 relevant past messages.
    3.  Injects them into "Relevant Context" block in prompt.

### B. Knowledge Graph (Entity Memory)
*   Structured memory about *Things* and *Relations*.
*   Example: `(User) --[LIKES]--> (Python)`, `(Project) --[USES]--> (SQLite)`.
*   **Use Case**: RPGs (Dungeon Crawl). The game remembers "Old Guard hates impulsive people" without needing the full chat log.

### C. The "Dreaming" Agent (Consolidation)
*   **Problem**: Context window fills up.
*   **Solution**: A background process runs at night (or idle time).
    *   Reads `raw_logs.txt`.
    *   Summarizes key decisions into `long_term_summary.md`.
    *   Deletes/Archives the raw logs.
*   **Analogy**: Human sleep/memory consolidation.

### D. "Ghost" Context (Ephemeral)
*   A hidden scratchpad that follows the conversation but isn't shown to the user.
*   The Agent writes thoughts to `<thought_process>` tags, which are fed back into the next turn but stripped from the UI.

## 3. Implementation Roadmap
1.  **Phase 1 (Manual)**: Implement `kiro memory save/load` in CLI.
2.  **Phase 2 (Auto)**: Add `--memory ./my_brain.md` flag to Agent. It auto-appends to this file.
3.  **Phase 3 (MCP)**: Create an `mcp-server-memory` that exposes these tools to *any* MCP-compliant client (Claude, Zed, Kirosu).
