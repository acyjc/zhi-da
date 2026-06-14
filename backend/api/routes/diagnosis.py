# 诊断分析路由——初诊(SSE流式)/历史查询
# 保存逻辑已迁移至 core/services/diagnosis_service.py
# SSE 流式逻辑已统一委托给 StudentAgentRuntime.run_stream()
# 旧 /re-evaluate 端点已移除（前端已迁移至 Agent /run-stream intent=re_evaluate）
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from config.settings import LLM_API_KEY
from core.models.diagnosis import DiagnoseRequest, DiagnosisResponse
from core.agent.student_runtime import StudentAgentRuntime
from core.services import diagnosis_service
from core.auth import get_current_identity, verify_student_access, Identity
# Re-export for backward compatibility (used by tests)
from core.services.diagnosis_service import normalize_top5_jobs as _normalize_top5_jobs, compute_dimension_changes as _compute_dimension_changes

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


# 全量初步诊断，通过 SSE 流式返回分析进度和结果
# 内部委托给 StudentAgentRuntime.run_stream()，保持旧 SSE 事件格式兼容
@router.post("/full")
async def full_diagnosis(
    req: DiagnoseRequest,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(req.student_id, identity)
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise HTTPException(503, "AI服务未就绪，请在后端配置 LLM_API_KEY 环境变量")

    runtime = StudentAgentRuntime()

    async def event_generator():
        async for event in runtime.run_stream(db, req.student_id, "diagnose", {}):
            if event.get("stage") == "result" and "result" in event:
                # 将 Agent Stream 的 result 格式转换为旧诊断格式
                agent_result = event["result"]
                data = agent_result.get("data", {})
                data["stage"] = "result"
                yield f"data: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
            elif event.get("stage") == "error":
                yield f"data: {json.dumps({'error': event.get('message', 'Unknown error')}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# 获取学生的诊断历史记录列表
@router.get("/history/{student_id}")
async def diagnosis_history(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    return await diagnosis_service.list_diagnosis_history(db, student_id)


# 获取单条诊断记录详情
@router.get("/{diagnosis_id}")
async def get_diagnosis(
    diagnosis_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    r = await diagnosis_service.get_diagnosis_by_id(db, diagnosis_id)
    if not r:
        return {"error": "Not found"}
    # 校验诊断记录归属当前学生
    verify_student_access(r.student_id, identity)
    try:
        return DiagnosisResponse(
            id=r.id, student_id=r.student_id, version=r.version,
            diagnosis_type=r.diagnosis_type, match_score=r.match_score or 0,
            dimension_scores=r.dimension_scores or {},
            dimension_changes=r.dimension_changes or {},
            gap_details=r.gap_details or [],
            top5_jobs=r.top5_jobs or [],
            growth_path=r.growth_path or {},
            career_advice=r.career_advice or "",
            ai_reasoning=r.ai_reasoning or {},
            ability_profile=r.ability_profile or {},
            explanations=r.explanations or {},
            confidence=r.confidence or {},
            ai_status=r.ai_status or "available",
            trigger_event=r.trigger_event or "",
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
    except Exception:
        return {"id": r.id, "error": "data corrupted", "version": r.version}
