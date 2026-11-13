"""Pure orchestration contracts; independent of Temporal, ACP and worker placement."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol
from uuid import uuid4


class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    ARCHITECT = "architect"
    IMPLEMENTER = "implementer"
    TESTER = "tester"
    REVIEWER = "reviewer"
    SECURITY = "security"
    INTEGRATOR = "integrator"


@dataclass(frozen=True)
class AgentTask:
    id: str
    role: AgentRole
    objective: str
    depends_on: tuple[str, ...] = ()
    read_only: bool = True
    required_artifacts: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    success: bool
    summary: str
    artifacts: dict[str, str] = field(default_factory=dict)
    findings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EngineeringPlan:
    id: str
    goal: str
    tasks: tuple[AgentTask, ...]
    approval_required: bool = True

    def __post_init__(self) -> None:
        ids = [task.id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate task ids")
        seen: set[str] = set()
        for task in self.tasks:
            if any(dep not in seen for dep in task.depends_on):
                raise ValueError(f"Task {task.id} depends on a missing or later task")
            seen.add(task.id)


class ExecutionPort(Protocol):
    """Implement with ACP, a local fake, or a future remote worker backend."""

    async def execute(self, task: AgentTask, context: dict[str, AgentResult]) -> AgentResult:
        ...


def validate_result(task: AgentTask, result: AgentResult) -> None:
    if result.task_id != task.id:
        raise ValueError(f"Mismatched task result for {task.id}")
    if not result.success:
        raise RuntimeError(f"{task.role.value} failed: {result.summary}")
    missing = set(task.required_artifacts) - set(result.artifacts)
    if missing:
        raise ValueError(f"{task.id} missing artifacts: {sorted(missing)}")


def build_feature_plan(goal: str, *, plan_id: str | None = None) -> EngineeringPlan:
    """Conservative playbook. Testing and review are independent after implementation.

    Artifacts are *references* (commit SHA, paths, report URIs), never bulky contents.
    Implementer owns an isolated workspace; review/testing consume its immutable revision.
    """
    if not goal.strip():
        raise ValueError("goal must not be empty")
    tasks = (
        AgentTask("research", AgentRole.RESEARCHER, f"Inspect repository and constraints for: {goal}",
                  required_artifacts=("research_report",)),
        AgentTask("design", AgentRole.ARCHITECT, f"Propose minimal change plan for: {goal}",
                  depends_on=("research",), required_artifacts=("design",)),
        AgentTask("implement", AgentRole.IMPLEMENTER, f"Implement: {goal}",
                  depends_on=("design",), read_only=False, required_artifacts=("revision",)),
        AgentTask("test", AgentRole.TESTER, "Verify implementation against acceptance criteria",
                  depends_on=("implement",), required_artifacts=("test_report",)),
        AgentTask("review", AgentRole.REVIEWER, "Independently review changes and correctness",
                  depends_on=("implement",), required_artifacts=("review_report",)),
        AgentTask("security", AgentRole.SECURITY, "Inspect security and privilege boundaries",
                  depends_on=("implement",), required_artifacts=("security_report",)),
        AgentTask("integrate", AgentRole.INTEGRATOR, "Prepare PR summary after all quality gates",
                  depends_on=("test", "review", "security"), read_only=False,
                  required_artifacts=("pr_summary",)),
    )
    return EngineeringPlan(id=plan_id or str(uuid4()), goal=goal, tasks=tasks)
