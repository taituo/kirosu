# 🧪 Study Ideas & Research Topics

A collection of technical explorations, gap analyses, and potential features for Kirosu.

## 🏢 Gap Analysis: Commercial Enterprise Stack vs Kirosu

Based on industry benchmarks (Microsoft Semantic Kernel, LangGraph, IBM Watson). Kirosu prioritizes *agile lightweight* architecture, but can bridge these gaps with targeted extensions.

### 1. Observability & Metrics (Gap: Medium)
*   **Commercial**: OTEL traces, Prometheus, SLA Dashboards.
*   **Kirosu Current**: Rich TUI, JSON logs, `/metrics` endpoint.
*   **Study Plan**:
    *   Expose a `/metrics` Prometheus-compatible endpoint (using `prometheus_client`).
    *   Add OpenTelemetry (OTEL) instrumentation to the `Hub` to trace task lifecycles across distributed agents.

### 2. Model Routing & Cost Control (Gap: Medium)
*   **Commercial**: Circuit breakers, cost quotas, fallback routing.
*   **Kirosu Current**: Simple TCP retry.
*   **Study Plan**:
    *   Implement a "Router Provider" (`kirosu.providers.Router`) that wraps other providers.
    *   Feature: Failover (Primary -> Fallback model).
    *   Feature: Token Bucket rate limiting per Tenant/User to prevent bill shock.

### 3. Plugin Marketplace (Gap: Medium)
*   **Commercial**: 100+ connectors (Salesforce, SAP).
*   **Kirosu Current**: "You code it".
*   **Study Plan**:
    *   Establish a standard "Tool Protocol" (Standardized Python Class structure).
    *   Create a `kirosu-contrib` repository/folder for community submitted tools (Gmail, Jira, Slack).
    *   Add `kirosu tool install <url>` CLI command.

### 4. Enterprise AuthN/Z (Gap: High)
*   **Commercial**: SAML, OIDC, RBAC.
*   **Kirosu Current**: Shared Secret Token (`KIRO_SWARM_KEY`).
*   **Study Plan**:
    *   Investigate integrating `Authlib` or `python-social-auth` into the Hub.
    *   Add `tenant_id` column to the `tasks` database to allow logical separation of data.

---

## 🦄 Wild Ideas (See WILD_IDEAS.md for more)
*   [ ] **Self-Replication**: Agent that deploys itself to new infrastructure.
*   [ ] **The "Internal Loop"**: Real-time monitoring within a single tool execution (Done in `live_odds_monitor.py`).
