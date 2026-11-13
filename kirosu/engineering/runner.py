"""Local orchestration runner useful for tests; worker dispatch is injected."""
from __future__ import annotations

import asyncio
from .frame import AgentResult, EngineeringPlan, ExecutionPort, validate_result


async def run_plan(plan: EngineeringPlan, executor: ExecutionPort) -> dict[str, AgentResult]:
    """Run ready tasks together; stop immediately on a failed gate.

    This is NOT durable. Deploy the Temporal workflow for crash recovery.
    """
    results: dict[str, AgentResult] = {}
    pending = {task.id: task for task in plan.tasks}
    while pending:
        ready = [task for task in pending.values() if all(dep in results for dep in task.depends_on)]
        if not ready:
            raise ValueError("Invalid plan: unresolved dependencies")
        # Only dependency results are passed. No shared mutable workspace assumptions.
        async def one(task):
            result = await executor.execute(task, {dep: results[dep] for dep in task.depends_on})
            validate_result(task, result)
            return task.id, result
        batch = await asyncio.gather(*(one(task) for task in ready))
        for task_id, result in batch:
            results[task_id] = result
            del pending[task_id]
    return results
