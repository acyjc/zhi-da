# 智能体对话记忆服务——管理学生与智能体的对话历史
# 统一记忆策略（Phase 6.4）：按意图分层写入 AgentConversation
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from db.models import AgentConversation
from core.utils.time import utc_now

logger = logging.getLogger(__name__)

# 记忆限制
MAX_MESSAGES = 10
MAX_AGE_DAYS = 7

# 记忆策略配置：定义每种意图是否写入记忆、写入内容类型
MEMORY_POLICY = {
    # ask: 写入完整消息（直接影响多轮问答）
    "ask": {"write": True, "mode": "full"},
    # diagnose: 写入摘要（保留关键诊断结论）
    "diagnose": {"write": True, "mode": "summary"},
    # continue_growth: 写入摘要（记录用户查看成长任务的上下文）
    "continue_growth": {"write": True, "mode": "summary"},
    # review_task: 写入摘要（记录提交证据和审核结论）
    "review_task": {"write": True, "mode": "summary"},
    # re_evaluate: 写入摘要（记录能力变化）
    "re_evaluate": {"write": True, "mode": "summary"},
    # navigate: 默认不写（导航行为价值低，避免噪音）
    "navigate": {"write": False, "mode": "none"},
}


async def append_message(
    db: AsyncSession,
    student_id: int,
    role: str,
    content: str,
    intent: str = "",
    metadata: dict = None,
) -> AgentConversation:
    """追加一条对话记录。"""
    record = AgentConversation(
        student_id=student_id,
        role=role,
        content=content[:2000],  # 限制单条长度
        intent=intent,
        metadata_=metadata or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def append_summary(
    db: AsyncSession,
    student_id: int,
    intent: str,
    summary: str,
    metadata: dict = None,
) -> AgentConversation | None:
    """按意图写入摘要记录（非完整对话）。

    用于 diagnose、continue_growth、review_task、re_evaluate 等意图，
    只保留关键结论，不保存冗长原文。
    """
    policy = MEMORY_POLICY.get(intent, {"write": False, "mode": "none"})
    if not policy.get("write"):
        return None

    record = AgentConversation(
        student_id=student_id,
        role="system_summary",
        content=summary[:500],  # 摘要更短限制
        intent=intent,
        metadata_=metadata or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def maybe_write_memory(
    db: AsyncSession,
    student_id: int,
    intent: str,
    user_message: str = "",
    assistant_response: str = "",
    summary: str = "",
    metadata: dict = None,
):
    """统一记忆写入入口——根据意图策略决定是否写入。

    - ask: 写入完整 user + assistant 消息。
    - diagnose / continue_growth / review_task / re_evaluate: 写入摘要。
    - navigate: 不写入。
    """
    policy = MEMORY_POLICY.get(intent, {"write": False, "mode": "none"})
    if not policy.get("write"):
        return

    mode = policy["mode"]
    try:
        if mode == "full":
            # 写入完整对话
            if user_message:
                await append_message(db, student_id, "user", user_message, intent=intent)
            if assistant_response:
                await append_message(
                    db, student_id, "assistant", assistant_response,
                    intent=intent, metadata=metadata,
                )
        elif mode == "summary":
            # 写入摘要
            if summary:
                await append_summary(db, student_id, intent, summary, metadata=metadata)
    except Exception as exc:
        logger.warning("写入对话记忆失败 (intent=%s): %s", intent, exc)


async def get_recent_messages(
    db: AsyncSession,
    student_id: int,
    limit: int = MAX_MESSAGES,
) -> list[dict]:
    """获取学生最近 N 条对话记录（包含 system_summary）。"""
    stmt = (
        select(AgentConversation)
        .where(AgentConversation.student_id == student_id)
        .order_by(AgentConversation.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    records = result.scalars().all()
    # 按时间正序返回（最旧在前）
    messages = []
    for r in reversed(records):
        if r.role == "system_summary":
            # 系统摘要必须带清晰标签，避免 LLM 误认为用户原话
            content = f"[系统记忆摘要——以下是系统自动记录的历史摘要，不是用户刚刚说的话]\n{r.content}"
            messages.append({
                "role": "system",
                "content": content,
                "intent": r.intent,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
        else:
            messages.append({
                "role": r.role,
                "content": r.content,
                "intent": r.intent,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })
    return messages


async def clear_old_messages(db: AsyncSession, before_days: int = MAX_AGE_DAYS) -> int:
    """清理超过指定天数的旧对话记录。"""
    cutoff = utc_now() - timedelta(days=before_days)
    stmt = delete(AgentConversation).where(AgentConversation.created_at < cutoff)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
