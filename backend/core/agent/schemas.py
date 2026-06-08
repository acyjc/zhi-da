# Agent 统一请求/响应 Schema
import uuid
from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


def generate_request_id() -> str:
    """生成唯一请求 ID，用于链路追踪。"""
    return uuid.uuid4().hex[:16]


class AgentIntent(str, Enum):
    """智能体意图类型。"""
    DIAGNOSE = "diagnose"
    CONTINUE_GROWTH = "continue_growth"
    REVIEW_TASK = "review_task"
    RE_EVALUATE = "re_evaluate"
    ASK = "ask"
    NAVIGATE = "navigate"


class AgentAction(str, Enum):
    """智能体返回的动作类型。"""
    ASK_FOR_INFO = "ask_for_info"
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    TASK_REVIEWED = "task_reviewed"
    RE_EVALUATION_COMPLETED = "re_evaluation_completed"
    ADVICE = "advice"
    ERROR = "error"


class AIStatus(str, Enum):
    """AI 服务状态。"""
    AVAILABLE = "available"
    MISSING_KEY = "missing_key"
    FALLBACK_RULE_BASED = "fallback_rule_based"
    PROVIDER_ERROR = "provider_error"
    SCHEMA_ERROR = "schema_error"


class NextAction(BaseModel):
    """建议的下一步操作。"""
    label: str
    intent: str
    payload: dict = Field(default_factory=dict)


class AgentRequest(BaseModel):
    """统一智能体请求。"""
    intent: AgentIntent
    payload: dict = Field(default_factory=dict)
    request_id: str = Field(default_factory=generate_request_id)


class AgentResult(BaseModel):
    """统一智能体响应。"""
    action: AgentAction
    message: str = ""
    data: dict = Field(default_factory=dict)
    next_actions: list[NextAction] = Field(default_factory=list)
    reasoning: dict = Field(default_factory=dict)
    ai_status: AIStatus = AIStatus.AVAILABLE
    request_id: str = ""
