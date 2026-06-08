# Agent API 路由——统一智能体接口
# 新入口：POST /api/agent/student/{student_id}/run
# 流式入口：POST /api/agent/student/{student_id}/run-stream
# 旧入口 /diagnose、/plan 保留兼容（仅供遗留测试使用，下次清理周期移除）
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.agent.schemas import AgentRequest
from core.agent.student_runtime import StudentAgentRuntime
from core.auth import require_student, verify_student_access, Identity

router = APIRouter(prefix="/api/agent", tags=["agent"])

# 全局 Runtime 实例
_runtime = StudentAgentRuntime()


# ============ 统一入口 ============

@router.post("/student/{student_id}/run")
async def agent_run(
    student_id: int,
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    """统一智能体入口。

    接收 intent + payload，返回统一的 AgentResult。
    自动生成 request_id 用于链路追踪。
    """
    verify_student_access(student_id, identity)
    request_id = req.request_id
    result = await _runtime.run(db, student_id, req.intent.value, req.payload, request_id=request_id)
    return result.model_dump()


@router.post("/student/{student_id}/run-stream")
async def agent_run_stream(
    student_id: int,
    req: AgentRequest,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    """流式智能体入口（SSE）。

    用于 diagnose、re_evaluate 和 ask 等长耗时意图，前端可实时看到进度。
    非流式意图会自动降级为单次结果返回。
    """
    verify_student_access(student_id, identity)
    request_id = req.request_id

    async def event_generator():
        async for event in _runtime.run_stream(db, student_id, req.intent.value, req.payload, request_id=request_id):
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============ 旧入口（仅供遗留测试使用，前端已迁移至 /run。下次清理周期可移除）============


@router.post("/student/{student_id}/diagnose")
async def agent_diagnose(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    """[DEPRECATED] 旧诊断入口——仅供遗留测试使用。

    前端已迁移至 POST /api/agent/student/{student_id}/run intent=diagnose。
    此端点在 test_agent_runtime.py 中仍有测试依赖，下次清理周期移除。
    """
    verify_student_access(student_id, identity)
    result = await _runtime.run(db, student_id, "diagnose", {})

    # 学生不存在时保持 404 兼容
    if result.action.value == "error" and "不存在" in result.message:
        return JSONResponse({"detail": result.message}, status_code=404)

    # 保持旧接口响应格式兼容
    if result.action.value == "ask_for_info":
        questions = result.data.get("followup_questions", [])
        return JSONResponse({
            "action": "ask_for_info",
            "reason": result.message,
            "completeness": result.data.get("completeness", 0),
            "missing_fields": result.data.get("missing_fields", []),
            "followup_questions": questions,
            "suggestion": "请补充以上信息后再进行诊断，以获得更准确的能力画像。",
        })

    if result.action.value == "diagnosis_completed":
        return JSONResponse({
            "action": "initial_diagnosis",
            "reason": "诊断已完成",
            "diagnosis": result.data,
            "next_actions": [a.model_dump() for a in result.next_actions],
        })

    if result.action.value == "error":
        return JSONResponse({"action": "error", "reason": result.message})

    return JSONResponse({
        "action": result.action.value,
        "reason": result.message,
        "data": result.data,
    })


@router.post("/student/{student_id}/plan")
async def agent_plan(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    """[DEPRECATED] 旧规划入口——仅供遗留测试使用。

    前端已迁移至 POST /api/agent/student/{student_id}/run intent=continue_growth。
    此端点在 test_agent_runtime.py 中仍有测试依赖，下次清理周期移除。
    """
    verify_student_access(student_id, identity)
    result = await _runtime.run(db, student_id, "continue_growth", {})

    # 保持旧接口兼容：无诊断时返回 need_diagnosis
    if result.data and result.data.get("diagnosis") is None:
        return JSONResponse({
            "action": "need_diagnosis",
            "suggestion": result.message,
        })

    return JSONResponse({
        "action": "plan",
        "latest_version": result.data.get("diagnosis_version"),
        "match_score": result.data.get("match_score", 0),
        "dimension_scores": result.data.get("dimension_scores", {}),
        "tasks": result.data.get("tasks", []),
        "growth_progress": {
            "completed": result.data.get("completed_count", 0),
            "total": result.data.get("total_count", 0),
        },
        "suggestion": result.message,
    })
