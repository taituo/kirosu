# Kirosu Examples & Demos 🧪

This directory contains various demonstrations of what the Kirosu Agent Framework can do.

## 🤖 Basic Chatbots
*   **`simple_chat.py`**: The bare-minimum logic to run a chatbot. Clean and simple.
*   **`chat_improved.py`**: A polished CLI chatbot with typing animations, bold text, and robust `Ctrl+C` handling.

## 🎲 Simulations & Games
*   **`bar_simulation.py`**: A multi-agent chaos simulation. 3 "Drunk" agents (Philosopher, Poet, Tourist) shout randomly, and 1 "Bartender" agent summarizes the noise into sanity. Demonstrates **Parallel Execution** (`asyncio.gather`) and **Output Aggregation**.
*   **`dungeon_crawl.py`**: An infinite procedural RPG. The Agent acts as Dungeon Master, generating rooms and refereeing combat on the fly. Demonstrates **Stateful Game Engine + Stateless AI Narrator**.
*   **`kuopion_tori.py`**: A text-adventure set in Kuopio during Midsummer. Features a heavy Savonian dialect, time limits, and survival mechanics. Demonstrates **Persona Injection** and **Dialect Simulation**.

## 🗺️ Context & Memory
*   **`chat_simple_context_carry.py`**: A proof-of-concept for **Native Context Management**. Agent A writes a story -> File -> Agent B critiques it. Simulates `/context save` and `/context load`.

## 📟 Retro & TUI
*   **`internet_dsl_lynx.py`**: A fully functional **Lynx Browser Simulator** (1997 Era).
    *   **Features**: Tab/Arrow navigation, Bookmarks (`a`/`v`), History (`b`), and LLM-generated Geocities pages.
    *   **Tech**: Built with `Textual` and `asyncio`.
*   **`real_browser.py`**: A **Real AI Browser** fueled by `codex --search`.
    *   **Usage**: Type "Current Stock Price of NVDA" or "Who won the game last night?".
    *   **Tech**: Injects `--search` flag into the Agent Provider.
*   **`teletext_browser.py`**: A **YLE Teksti-TV Simulator** (ASCII/TUI).
    *   **Features**: 3-digit page navigation (100, 200, 300).
    *   **Style**: 40x24 char grid, block headers, pixel-perfect nostalgia.

## 📊 Business Logic
*   **`live_odds_monitor.py`**: (Conceptual) A monitoring agent structure.
*   **`three_worker_demo.py`**: Demonstrates isolated workspaces for multiple workers.

## Usage
Run any demo using `uv run`:
```bash
export KIRO_PROVIDER=codex
uv run examples/kuopion_tori.py
```
