# 🗺️ Kirosu Long-Term Roadmap & Master Plan (2025)

This document consolidates the architectural vision, strategic insights, and future roadmap for Kirosu, synthesized from our "Think Tank" sessions.

---

## 🏗️ 1. Architectural Vision

### A. The "Headless Platform" Pattern
*   **Concept**: Kirosu is a **Backend Engine**, not a finished consumer product. It speaks TCP/JSON-RPC.
*   **Application**: It is designed to be the "Engine" under a custom "Body" (e.g., a React Dashboard, Mobile App, or Slack Bot).
*   **Implementation**: A lightweight `FastAPI` Gateway sitting in front of the Hub allows standard REST clients to interact with the Swarm.

### B. "The Internal Loop" (Real-Time / HFT)
*   **Problem**: Default Hub polling (~1s) is too slow for High-Frequency Trading or Live Betting.
*   **Solution**: The **Internal Loop Pattern**. An Agent executes a tool that runs a local `while True` loop interacting with WebSockets (<10ms latency).
*   **Logic**: "Python does the work, LLM makes the decision." Only actionable **signals** are sent back to the Hub as tasks.
*   **Proven By**: `examples/live_odds_monitor.py`.

### C. "Hybrid Swarm" (Tiered Intelligence)
*   **Concept**: Optimize cost vs intelligence by mixing models. 
*   **Tier 1 (Infantry - Execution)**: RunPod/vLLM (Llama-3, Mistral, GLM-4, Qwen). Low cost ($0.30/h). Use for mass data ingestion, monitoring, and sanitization.
*   **Tier 2 (Generals - Strategy)**: Frontier Models (Claude 3.5 Sonnet, GPT-5 Codex, Gemini Ultra). High cost. Use for complex reasoning, coding, and final verification.
*   **Tier 3 (Connectors - Specialists)**: `LangChainProvider` or Custom APIs. Connects to corporate RAG pipelines or proprietary Brains.
*   **Implementation**: Kirosu's `Provider` interface (`kirosu/providers.py`) acts as the "Universal Adapter" to mix and match these in a single swarm.

### D. "Code First" (The Anti-LangFlow)
*   **Insight**: **"Kirosu is LangFlow without the mouse."**
*   **Philosophy**: Visual Node Editors are great for prototypes but hit a glass ceiling. Kirosu provides the same graph-based logic (Node A -> Node B) but expressed in pure Python.
*   **Advantage**: Unlimited control, standard debugging tools (`pdb`), and direct database/API access.

---

## 💼 2. Enterprise Gap Analysis

Compared to commercial stacks (Microsoft Semantic Kernel, LangGraph, IBM Watson):

| Feature | Missing in Kirosu | Quick Fix (Roadmap) |
| :--- | :--- | :--- |
| **Observability** | Visual Dashboards | Export `/metrics` to Prometheus + Grafana. |
| **Failover** | Auto-Retry Logic | Wrap Providers with `tenacity` library. |
| **Cost Control** | Rate Limits | Implement Token Bucket per Agent. |
| **Auth** | SSO/SAML | Add OAuth Gateway (Keycloak) in front of API. |

---

## 🦁 3. Use Case Library (Summary)

*See `WILD_IDEAS.md` for the full 60-item catalog.*

### Top 5 "Real Life" Implementations
1.  **Live Odds Monitor**: Real-time arbitrage watcher (Internal Loop).
2.  **Verified Chain**: Maker -> Checker -> Translator -> Checker (Robust Pipeline).
3.  **Crawler Swarm**: 24/7 Data Ingestion Agents (Archivists).
4.  **The Researcher**: Pattern matching on historical datasets ("Moneyball" for data).
5.  **Self-Healing Dev**: CI/CD Loop that fixes its own bugs.

---

## 🛠️ 4. Immediate Roadmap (Next Steps)

1.  **Observability Stack**: Deploy a Grafana dashboard to visualize Task Throughput and Agent Latency.
2.  **API Gateway**: Create `kirosu/api.py` to expose the Hub via HTTP.
3.  **Hybrid Demo**: Create a demo script launching a local Llama agent alongside a Claude agent.

> *"Kirosu is like Linux: You get absolute power, but you own the responsibility."*
