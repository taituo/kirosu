"""Optional Temporal bridge. Install temporalio to use this workflow.

The execute_agent_activity must be registered by your worker implementation.
It receives serializable AgentTask / context payloads, calls the ACP adapter,
and returns an AgentResult mapping. Activities are the retry boundary.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta

from temporalio import workflow

from .frame import AgentRole, AgentTask, EngineeringPlan, AgentResult, validate_result


@workflow.defn
class EngineeringWorkflow:
    @workflow.run
    async def run(self, plan: EngineeringPlan) -> dict[str, AgentResult]:
        completed: dict[str, AgentResult] = {}
        pending = {task.id: task for task in plan.tasks}
        while pending:
            ready = [task for task in pending.values() if all(d in completed for d in task.depends_on)]
            if not ready:
                raise ValueError("Unresolvable engineering task graph")

            async def execute(task: AgentTask) -> tuple[str, AgentResult]:
                # Workflow code only schedules activities; agent processes live outside it.
                result = await workflow.execute_activity(
                    "execute_agent_activity",
                    args=[task, {dep: completed[dep] for dep in task.depends_on}],
                    start_to_close_timeout=timedelta(minutes=30),
                    # Retries require idempotent worker behavior using task.id + plan.id.
                )
                validate_result(task, result)
                return task.id, result

            for task_id, result in await asyncio.gather(*(execute(task) for task in ready)):
                completed[task_id] = result
                del pending[task_id]
        # Integrator creates a PR summary only; publishing needs external approval.
        return completed
