# Agent Trace Service——记录每次 Agent 决策的追踪数据
# 用于可解释性展示、调试和答辩演示
from __future__ import annotations

import logging
import time
from datetime import datetime, UTC

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AgentTrace

logger = logging.getLogger(__name__)


async def write_trace(
    db: AsyncSession,
    *,
    request_id: str,
    student_id: int,
    intent: str = "",
    selected_skill: str = "",
    used_tools: list[str] | None = None,
    rejected_tools: list[dict] | None = None,
    input_summary: str = "",
    output_action: str = "",
    confidence: float = 0.0,
    limits: list[str] | None = None,
    duration_ms: int = 0,
    fallback_used: bool = False,
) -> AgentTrace:
    """写入一条 Agent 决策追踪记录。

    Args:
        db: 异步数据库会话。
        request_id: 请求 ID（与 AgentResult.request_id 对齐）。
        student_id: 学生 ID。
        intent: 用户意图。
        selected_skill: Planner 选择的 Skill 名称。
        used_tools: 实际调用的工具列表。
        rejected_tools: 被拒绝的工具及原因。
        input_summary: 用户输入摘要（截断，不存完整 Prompt）。
        output_action: Agent 输出动作（AgentAction.value）。
        confidence: 置信度。
        limits: 能力边界说明列表。
        duration_ms: 执行耗时（毫秒）。
        fallback_used: 是否使用了降级策略。

    Returns:
        创建的 AgentTrace ORM 对象。
    """
    trace = AgentTrace(
        request_id=request_id,
        student_id=student_id,
        intent=intent,
        selected_skill=selected_skill,
        used_tools=used_tools or [],
        rejected_tools=rejected_tools or [],
        input_summary=input_summary[:500] if input_summary else "",
        output_action=output_action,
        confidence=round(max(0.0, min(1.0, confidence)), 2),
        limits=limits or [],
        duration_ms=duration_ms,
        fallback_used=1 if fallback_used else 0,
    )
    db.add(trace)
    try:
        await db.commit()
        await db.refresh(trace)
    except Exception as exc:
        await db.rollback()
        logger.warning("Agent Trace 写入失败: %s", exc)
    return trace


async def get_traces_by_student(
    db: AsyncSession,
    student_id: int,
    limit: int = 20,
) -> list[dict]:
    """按学生 ID 查询最近的 Agent Trace 列表。

    Args:
        db: 异步数据库会话。
        student_id: 学生 ID。
        limit: 返回记录数量上限。

    Returns:
        Trace 记录字典列表，按时间倒序。
    """
    result = await db.execute(
        select(AgentTrace)
        .where(AgentTrace.student_id == student_id)
        .order_by(desc(AgentTrace.created_at))
        .limit(limit)
    )
    traces = result.scalars().all()
    return [_trace_to_dict(t) for t in traces]


async def get_trace_by_request_id(
    db: AsyncSession,
    request_id: str,
) -> dict | None:
    """按 request_id 查询单条 Trace。

    Args:
        db: 异步数据库会话。
        request_id: 请求 ID。

    Returns:
        Trace 字典，不存在则返回 None。
    """
    result = await db.execute(
        select(AgentTrace).where(AgentTrace.request_id == request_id)
    )
    trace = result.scalar_one_or_none()
    return _trace_to_dict(trace) if trace else None


def _trace_to_dict(trace: AgentTrace | None) -> dict:
    """将 ORM 对象转为字典。"""
    if trace is None:
        return {}
    return {
        "id": trace.id,
        "request_id": trace.request_id,
        "student_id": trace.student_id,
        "intent": trace.intent,
        "selected_skill": trace.selected_skill,
        "used_tools": trace.used_tools or [],
        "rejected_tools": trace.rejected_tools or [],
        "input_summary": trace.input_summary or "",
        "output_action": trace.output_action,
        "confidence": trace.confidence,
        "limits": trace.limits or [],
        "duration_ms": trace.duration_ms,
        "fallback_used": bool(trace.fallback_used),
        "created_at": trace.created_at.isoformat() if trace.created_at else None,
    }


class TraceTimer:
    """简单的计时上下文管理器，用于计算 Agent 执行耗时。

    用法:
        timer = TraceTimer()
        timer.start()
        # ... do work ...
        duration_ms = timer.elapsed_ms()
    """

    def __init__(self) -> None:
        self._start: float = 0.0

    def start(self) -> None:
        self._start = time.monotonic()

    def elapsed_ms(self) -> int:
        if self._start == 0.0:
            return 0
        return int((time.monotonic() - self._start) * 1000)
