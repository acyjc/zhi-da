# 工具注册表——统一管理智能体可调用工具的注册、查询与执行
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from core.agent.runtime import ContextLoader
from core.services import diagnosis_service

logger = logging.getLogger(__name__)


# ---- 工具调用结果 ----
@dataclass
class ToolResult:
    """工具调用结果封装。"""
    success: bool
    data: Any = None
    error: str = ""
    source: str = ""  # 工具名称，用于追踪数据来源


# ---- 工具注册表 ----
class ToolRegistry:
    """注册 AI 可用工具，支持定义查询、OpenAI 格式输出和异步调用。"""

    def __init__(self, allowed_tools: set[str] | None = None) -> None:
        self._tools: dict[str, dict] = {}
        self._allowed_tools = allowed_tools

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
        read_only: bool = True,
        allowed_intents: list[str] | None = None,
        source: str = "",
    ) -> None:
        """注册一个工具。

        Args:
            name: 工具唯一名称。
            description: 工具描述（供 LLM 理解用途）。
            parameters: JSON Schema 格式的参数定义。
            handler: 异步可调用对象，执行工具逻辑。
            read_only: 是否为只读工具（不修改数据），默认 True。
            allowed_intents: 允许使用该工具的意图列表，None 表示所有意图可用。
            source: 数据来源标识（如 "student_service", "diagnosis_service"）。

        Raises:
            ValueError: 工具名称已存在。
        """
        if name in self._tools:
            raise ValueError(f"工具 '{name}' 已注册，不允许重复注册")
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
            "read_only": read_only,
            "allowed_intents": allowed_intents,
            "source": source or name,
        }

    def get(self, name: str) -> dict | None:
        """获取指定工具的定义，不存在则返回 None。"""
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        """返回所有工具定义列表（用于 LLM 上下文）。"""
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
                "read_only": t["read_only"],
                "source": t.get("source", t["name"]),
            }
            for t in self._tools.values()
        ]

    def list_openai_tools(self) -> list[dict]:
        """返回 OpenAI function calling 格式的工具定义。"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    def is_tool_allowed(self, name: str) -> bool:
        """检查工具是否在允许列表中。"""
        if self._allowed_tools is None:
            return name in self._tools
        return name in self._allowed_tools

    def is_tool_allowed_for_intent(self, name: str, intent: str) -> bool:
        """检查工具是否允许在指定意图下使用。"""
        tool = self._tools.get(name)
        if not tool:
            return False
        allowed_intents = tool.get("allowed_intents")
        if allowed_intents is None:
            return True  # 不限制意图
        return intent in allowed_intents

    def validate_tool_suggestions(self, suggested: list[str], intent: str = "") -> list[str]:
        """验证 LLM 建议的工具列表，返回允许的工具名。

        同时检查全局 allowlist 和 intent 级白名单。

        Args:
            suggested: LLM 建议的工具名称列表。
            intent: 当前意图名称，用于检查 allowed_intents。

        Returns:
            允许执行的工具名列表。
        """
        approved = []
        for name in suggested:
            if not self.is_tool_allowed(name):
                continue
            if intent and not self.is_tool_allowed_for_intent(name, intent):
                continue
            approved.append(name)
        return approved

    def get_rejected_tools(self, suggested: list[str], intent: str = "") -> list[dict]:
        """返回被拒绝的工具及拒绝原因（用于 reasoning 记录）。

        Args:
            suggested: LLM 建议的工具名称列表。
            intent: 当前意图名称。

        Returns:
            [{"name": "tool_name", "reason": "reason"}]
        """
        rejected = []
        for name in suggested:
            if name not in self._tools:
                rejected.append({"name": name, "reason": "工具未注册"})
            elif not self.is_tool_allowed(name):
                rejected.append({"name": name, "reason": "不在全局允许列表中"})
            elif intent and not self.is_tool_allowed_for_intent(name, intent):
                rejected.append({"name": name, "reason": f"不允许在 {intent} 意图下使用"})
        return rejected

    async def call(self, name: str, **kwargs) -> ToolResult:
        """调用指定工具并返回 ToolResult。

        执行前做参数校验：student_id / job_id 等必要参数不为空。

        Args:
            name: 工具名称。
            **kwargs: 传递给工具 handler 的参数。

        Returns:
            ToolResult: 封装调用结果或错误信息。
        """
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"工具 {name} 未注册", source=name)

        # 必要参数校验
        required_params = tool.get("parameters", {}).get("required", [])
        for param in required_params:
            value = kwargs.get(param)
            if not value or (isinstance(value, str) and not value.strip()):
                return ToolResult(
                    success=False,
                    error=f"工具 {name} 缺少必要参数: {param}",
                    source=name,
                )

        try:
            result = await tool["handler"](**kwargs)
            return ToolResult(success=True, data=result, source=name)
        except Exception as exc:
            logger.error("工具 %s 执行失败: %s", name, exc)
            return ToolResult(success=False, error=str(exc), source=name)


# ---- 工具 handler 实现 ----

async def _get_student_profile(db: AsyncSession, student_id: int = 0) -> dict | None:
    """获取学生画像。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    return await ContextLoader.load_student(db, student_id)


async def _get_latest_diagnosis(db: AsyncSession, student_id: int = 0) -> dict | None:
    """获取学生最新诊断结果。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    diag = await diagnosis_service.get_latest_diagnosis(db, student_id)
    if not diag:
        return None
    return {
        "id": diag.id,
        "version": diag.version,
        "diagnosis_type": diag.diagnosis_type,
        "match_score": diag.match_score,
        "dimension_scores": diag.dimension_scores or {},
        "dimension_changes": diag.dimension_changes or {},
        "gap_details": diag.gap_details or [],
        "top5_jobs": diag.top5_jobs or [],
        "career_advice": diag.career_advice or "",
        "ai_status": diag.ai_status or "available",
        "created_at": diag.created_at.isoformat() if diag.created_at else None,
    }


async def _get_diagnosis_history(db: AsyncSession, student_id: int = 0, limit: int = 3) -> list[dict]:
    """获取学生诊断历史摘要。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    return await ContextLoader.get_diagnosis_history(db, student_id, limit)


async def _get_growth_tasks(db: AsyncSession, student_id: int = 0) -> dict:
    """获取学生成长任务进度。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    return await ContextLoader.get_growth_progress(db, student_id)


async def _get_authorizations(db: AsyncSession, student_id: int = 0) -> list[dict]:
    """获取学生有效授权列表。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    return await ContextLoader.get_student_authorizations(db, student_id)


async def _get_visible_jobs(db: AsyncSession, student_id: int = 0) -> list[dict]:
    """获取当前可投递的岗位列表。"""
    if not student_id:
        raise ValueError("student_id 不能为空")
    return await ContextLoader.get_active_jobs(db)


async def _get_job_detail(db: AsyncSession, job_id: str = "") -> dict | None:
    """获取岗位能力模型详情。"""
    if not job_id:
        raise ValueError("job_id 不能为空")
    return await ContextLoader.get_job_ability_model(db, job_id)


# ---- 工具参数 JSON Schema 定义 ----

_STUDENT_ID_PARAM = {
    "type": "object",
    "properties": {
        "student_id": {
            "type": "string",
            "description": "学生 ID",
        },
    },
    "required": ["student_id"],
}

_JOB_ID_PARAM = {
    "type": "object",
    "properties": {
        "job_id": {
            "type": "string",
            "description": "岗位 ID",
        },
    },
    "required": ["job_id"],
}

_DIAGNOSIS_HISTORY_PARAMS = {
    "type": "object",
    "properties": {
        "student_id": {
            "type": "string",
            "description": "学生 ID",
        },
        "limit": {
            "type": "integer",
            "description": "返回记录数量上限，默认 3",
            "default": 3,
        },
    },
    "required": ["student_id"],
}


# ---- 工厂函数 ----

def register_all_tools(db: AsyncSession, student_id: int) -> ToolRegistry:
    """创建 ToolRegistry 并注册第一批只读工具。

    每个工具包含：name, description, parameters, handler, read_only, allowed_intents, source。

    Args:
        db: 异步数据库会话。
        student_id: 当前学生 ID，用于绑定工具调用的上下文。

    Returns:
        ToolRegistry: 已注册所有工具的注册表实例。
    """
    registry = ToolRegistry()

    registry.register(
        name="get_student_profile",
        description="获取学生画像信息，包括技能、项目经验、学业基础等",
        parameters=_STUDENT_ID_PARAM,
        handler=_get_student_profile,
        read_only=True,
        source="student_service",
    )

    registry.register(
        name="get_latest_diagnosis",
        description="获取学生最新一次诊断结果，包含匹配分数、维度分数和差距分析",
        parameters=_STUDENT_ID_PARAM,
        handler=_get_latest_diagnosis,
        read_only=True,
        source="diagnosis_service",
    )

    registry.register(
        name="get_diagnosis_history",
        description="获取学生历史诊断记录摘要列表，可指定返回条数",
        parameters=_DIAGNOSIS_HISTORY_PARAMS,
        handler=_get_diagnosis_history,
        read_only=True,
        source="diagnosis_service",
    )

    registry.register(
        name="get_growth_tasks",
        description="获取学生成长任务进度，包括任务列表和完成统计",
        parameters=_STUDENT_ID_PARAM,
        handler=_get_growth_tasks,
        read_only=True,
        source="growth_task_service",
    )

    registry.register(
        name="get_authorizations",
        description="获取学生的有效企业授权列表，包含岗位和企业信息",
        parameters=_STUDENT_ID_PARAM,
        handler=_get_authorizations,
        read_only=True,
        source="authorization_service",
    )

    registry.register(
        name="get_visible_jobs",
        description="获取当前所有可投递的岗位列表（企业已审核通过的岗位）",
        parameters=_STUDENT_ID_PARAM,
        handler=_get_visible_jobs,
        read_only=True,
        source="job_service",
    )

    registry.register(
        name="get_job_detail",
        description="获取指定岗位的能力模型详情，包括技术技能、软技能、领域知识要求及权重配置",
        parameters=_JOB_ID_PARAM,
        handler=_get_job_detail,
        read_only=True,
        allowed_intents=["ask"],  # 只在 ask 意图下允许按 job_id 查询
        source="job_service",
    )

    return registry
