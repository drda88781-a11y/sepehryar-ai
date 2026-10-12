"""
Base contracts, shared models, and Blackboard state for Sepehryar AI Core Multi-Agent system.
"""
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field
import time


class AgentRole(str, Enum):
    MASTER = "master"
    DATABASE = "database"
    SQL = "sql"
    PROCEDURE = "procedure"
    CODE = "code"
    DEBUG = "debug"
    ARCHITECTURE = "architecture"
    CRITIC = "critic"


class CriticVerdict(str, Enum):
    APPROVED = "approved"
    APPROVED_WITH_WARNINGS = "approved_with_warnings"
    REJECTED = "rejected"


class AgentTask(BaseModel):
    task_id: str
    role: AgentRole
    goal: str
    context: dict[str, Any] = Field(default_factory=dict)
    priority: int = 1


class AgentResult(BaseModel):
    task_id: str
    role: AgentRole
    success: bool = True
    summary: str = ""
    findings: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class CriticReview(BaseModel):
    verdict: CriticVerdict = CriticVerdict.APPROVED
    confidence_score: float = Field(default=0.95, ge=0.0, le=1.0)
    safety_checks: list[str] = Field(default_factory=list)
    architecture_compatibility: bool = True
    data_integrity_safe: bool = True
    concerns_or_critiques: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    hypothesis_id: str
    statement: str
    basis: str
    confidence: float = 0.8
    tested: bool = False
    supported: bool = True


class ReasoningStep(BaseModel):
    step_number: int
    agent_role: AgentRole
    stage_title: str
    reasoning_description: str
    timestamp: float = Field(default_factory=time.time)


class Blackboard(BaseModel):
    """
    Shared working memory accessible by Master Agent and all specialized agents during execution.
    """
    session_id: str = "default"
    user_query: str
    database_name: Optional[str] = None
    target_entities: list[str] = Field(default_factory=list)
    active_hypotheses: list[Hypothesis] = Field(default_factory=list)
    reasoning_chain: list[ReasoningStep] = Field(default_factory=list)
    agent_results: dict[str, AgentResult] = Field(default_factory=dict)
    generated_sql: Optional[str] = None
    generated_code: Optional[str] = None
    generated_sp: Optional[str] = None
    critic_reviews: list[CriticReview] = Field(default_factory=list)
    final_solution: Optional[str] = None

    def add_step(self, role: AgentRole, stage_title: str, description: str) -> None:
        step_no = len(self.reasoning_chain) + 1
        self.reasoning_chain.append(
            ReasoningStep(
                step_number=step_no,
                agent_role=role,
                stage_title=stage_title,
                reasoning_description=description,
            )
        )

    def record_result(self, result: AgentResult) -> None:
        self.agent_results[result.role.value] = result


class BaseSpecializedAgent:
    """Abstract base class for all specialized agents in Sepehryar AI Core."""

    def __init__(self, role: AgentRole, persian_title: str, description: str):
        self.role = role
        self.persian_title = persian_title
        self.description = description

    def execute(self, task: AgentTask, blackboard: Blackboard) -> AgentResult:
        """Execute a specialized subtask using local knowledge, live tools, and deductive inference."""
        raise NotImplementedError("Each specialized agent must implement execute()")
