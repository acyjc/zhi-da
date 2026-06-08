# Agent Trace API——查询 Agent 决策追踪记录
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_identity, verify_student_access
from core.services import agent_trace_service
from db.database import get_db

router = APIRouter(prefix="/api/agent-traces", tags=["agent-traces"])


@router.get("/student/{student_id}")
async def list_student_traces(
    student_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    identity=Depends(get_current_identity),
):
    """获取指定学生的 Agent 决策追踪列表（按时间倒序）。

    需要学生本人或管理员身份。
    """
    verify_student_access(student_id, identity)
    traces = await agent_trace_service.get_traces_by_student(db, student_id, limit=limit)
    return {"traces": traces, "total": len(traces)}


@router.get("/request/{request_id}")
async def get_trace_by_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    identity=Depends(get_current_identity),
):
    """按 request_id 查询单条 Agent Trace。"""
    trace = await agent_trace_service.get_trace_by_request_id(db, request_id)
    if not trace:
        return {"trace": None, "message": "Trace not found"}
    # 权限检查：只有学生本人或管理员可查看
    if identity.role == "student" and trace.get("student_id") != identity.student_id:
        return {"trace": None, "message": "Access denied"}
    return {"trace": trace}
