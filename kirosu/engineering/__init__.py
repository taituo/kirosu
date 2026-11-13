"""Engineering-agent frame: contracts, playbooks and pluggable execution."""
from .frame import AgentRole, AgentTask, AgentResult, EngineeringPlan, ExecutionPort, build_feature_plan, validate_result

__all__ = ["AgentRole", "AgentTask", "AgentResult", "EngineeringPlan", "ExecutionPort", "build_feature_plan", "validate_result"]
