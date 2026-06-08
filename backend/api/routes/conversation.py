"""对话历史 API——获取学生的多轮对话记录。"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.auth import get_current_identity, verify_student_access, Identity

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/{student_id}/messages")
async def get_messages(
    student_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    from core.services.agent_memory_service import get_recent_messages
    messages = await get_recent_messages(db, student_id, limit=limit)
    return {"messages": messages, "student_id": student_id}
