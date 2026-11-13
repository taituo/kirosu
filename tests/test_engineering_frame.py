import asyncio
import pytest

from kirosu.engineering import AgentResult, build_feature_plan, validate_result
from kirosu.engineering.runner import run_plan


class FakeExecutor:
    async def execute(self, task, context):
        assert set(context) == set(task.depends_on)
        return AgentResult(
            task_id=task.id, success=True, summary="ok",
            artifacts={name: f"artifact://{task.id}/{name}" for name in task.required_artifacts},
        )


def test_plan_dependencies_and_roles():
    plan = build_feature_plan("Add login", plan_id="test-1")
    assert len(plan.tasks) == 7
    assert next(t for t in plan.tasks if t.id == "integrate").depends_on == ("test", "review", "security")


def test_missing_artifacts_fails():
    task = build_feature_plan("Fix bug").tasks[0]
    with pytest.raises(ValueError, match="missing artifacts"):
        validate_result(task, AgentResult(task.id, True, "ok"))


def test_run_plan():
    result = asyncio.run(run_plan(build_feature_plan("Add login"), FakeExecutor()))
    assert len(result) == 7
    assert "integrate" in result
