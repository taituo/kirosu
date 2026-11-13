# Kiro V3 engineering-agent frame (initial scaffold)

This frame separates **what runs** from **where/how workers run**. Kubernetes,
pods, shared volumes, and process spawning are intentionally out of scope.

## Contracts

- `AgentTask`: role, objective, dependencies, permissions, required artifacts.
- `AgentResult`: success, summary, artifact references, findings.
- `ExecutionPort`: asynchronous adapter boundary. Implement with an ACP client
  or a mock; this scaffold does **not** claim an ACP transport implementation.
- `EngineeringPlan`: validated ordered DAG of tasks.
- `validate_result`: fail closed for missing artifacts or unsuccessful work.

## Feature playbook

`research → design → implement → (test || review || security) → integrate`

Seven specializations: researcher, architect, implementer, tester, reviewer,
security analyst, integrator. An integrator returns a PR summary; it does not
automatically merge or publish. A human approval gate is a required future
production integration before any external write/PR creation.

## Temporal boundary

`kirosu.engineering.temporal_workflow.EngineeringWorkflow` is an optional
workflow definition (requires `temporalio`). Your Temporal worker must register
an activity named `execute_agent_activity`, convert wire payloads into contract
types, and delegate to an `ExecutionPort`. Use a stable idempotency key
`(plan.id, task.id)` for any side effects. Persist artifacts outside Temporal
history and return only immutable references.

The included `run_plan` provides a non-durable local fake for unit tests and
does not replace Temporal.

## Execution isolation and safety

- Implementation occurs in an isolated revision/worktree; reviewers use that
  exact immutable revision, not a moving branch.
- Read-only roles have no write/tool permission. Enforce permissions in the
  adapter/worker, not just in prompts.
- Never run arbitrary agent-provided shell commands with blanket trust flags.
- Stop on failed tests, blocking review, or missing reports.
- Explicit review, retry policy, cancellation, and human approval will be
  connected when the real ACP adapter and runtime are added.

## Next integration

1. Define the ACP session lifecycle in an adapter satisfying `ExecutionPort`.
2. Add a Temporal worker activity with stable serialization and idempotency.
3. Add cancellation, approval signals, and revision/quality-gate verification.
4. Hook the playbook into the existing Kirosu task entry point.

No infrastructure implementation is assumed.
