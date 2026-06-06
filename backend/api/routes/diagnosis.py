# 诊断分析路由——初诊/再诊(SSE流式)/历史查询
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select, func
from db.database import get_db, async_session
from db.models import DiagnosisResult as DiagORM, Student as StudentORM
from config.settings import LLM_API_KEY
from core.models.diagnosis import DiagnoseRequest, ReEvaluateRequest, DiagnosisResponse
from core.harness.runner import PipelineRunner
from core.harness.step import PipelineState
from core.pipelines.diagnosis_pipeline import ProfileStep, MatchStep, GapStep, PathStep, AdviceStep

router = APIRouter(prefix="/api/diagnosis", tags=["diagnosis"])


def _compute_dimension_changes(current: dict, previous: dict) -> dict:
    if not previous:
        return {}
    changes = {}
    for key in set(list(current.keys()) + list(previous.keys())):
        cur_val = current.get(key, 0)
        prev_val = previous.get(key, 0)
        diff = round(cur_val - prev_val, 3)
        if abs(diff) > 0.001:
            changes[key] = diff
    return changes


async def _get_student_dict(db: AsyncSession, student_id: str) -> dict:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {}
    return {
        "id": student.id, "name": student.name, "grade": student.grade,
        "major": student.major, "target_job": student.target_job,
        "tech_skills": student.tech_skills or {},
        "project_exp": student.project_exp or [],
        "soft_skills": student.soft_skills or {},
        "domain_knowledge": student.domain_knowledge or {},
        "resume_text": student.resume_text or "",
    }


async def _save_diagnosis(db: AsyncSession, student_id: str, state: PipelineState,
                          diagnosis_type: str = "initial", trigger_event: str = "",
                          previous_diag_id: str = "") -> DiagnosisResponse:
    match_result = dict(state.get("match_result", {}))
    match_result.setdefault("previous_dimension_scores", state.extra.get("previous_dimension_scores", {}))
    result = await db.execute(
        select(func.max(DiagORM.version)).where(DiagORM.student_id == student_id))
    max_ver = result.scalar() or 0
    version = max_ver + 1 if diagnosis_type != "initial" else 1

    diag = DiagORM(
        student_id=student_id, version=version, diagnosis_type=diagnosis_type,
        match_score=match_result.get("match_score", 0),
        dimension_scores=match_result.get("dimension_scores", {}),
        dimension_changes=_compute_dimension_changes(match_result.get("dimension_scores", {}), match_result.get("previous_dimension_scores", {})),
        gap_details=match_result.get("gap_details", []),
        top5_jobs=match_result.get("top5_jobs", []),
        growth_path=state.get("growth_path", {}),
        career_advice=state.get("career_advice", ""),
        ai_reasoning=state.get("ai_reasoning", {}),
        trigger_event=trigger_event,
    )
    db.add(diag)
    await db.commit()
    await db.refresh(diag)
    try:
        return DiagnosisResponse(
            id=diag.id, student_id=diag.student_id, version=diag.version,
            diagnosis_type=diag.diagnosis_type, match_score=diag.match_score,
            dimension_scores=diag.dimension_scores or {},
            dimension_changes=diag.dimension_changes or {},
            gap_details=diag.gap_details or [],
            top5_jobs=diag.top5_jobs or [],
            growth_path=diag.growth_path or {},
            career_advice=diag.career_advice or "",
            ai_reasoning=diag.ai_reasoning or {},
            trigger_event=diag.trigger_event or "",
            created_at=diag.created_at.isoformat() if diag.created_at else None,
        )
    except Exception:
        return DiagnosisResponse(
            id=diag.id, student_id=diag.student_id, version=diag.version,
            diagnosis_type=diag.diagnosis_type, match_score=diag.match_score or 0,
            dimension_scores={}, dimension_changes={}, gap_details=[],
            top5_jobs=[], growth_path={}, career_advice="",
            ai_reasoning={}, trigger_event=trigger_event or "",
            created_at=diag.created_at.isoformat() if diag.created_at else None,
        )


async def _run_pipeline_sse(student_id: str, db: AsyncSession,
                            diagnosis_type: str, trigger_event: str) -> StreamingResponse:
    student_dict = await _get_student_dict(db, student_id)
    if not student_dict:
        async def err_gen():
            yield f"data: {json.dumps({'error': 'Student not found'})}\n\n"
        return StreamingResponse(err_gen(), media_type="text/event-stream")

    prev_result = await db.execute(
        select(DiagORM).where(DiagORM.student_id == student_id).order_by(desc(DiagORM.version)).limit(1))
    prev_diag = prev_result.scalar_one_or_none()

    state = PipelineState(input=student_dict, extra={
        "previous_dimension_scores": prev_diag.dimension_scores if prev_diag else {},
    })
    async def _fallback_handler(step_name: str, state: PipelineState, error: Exception):
        import logging
        logging.getLogger(__name__).warning(f"Step {step_name} failed: {error}, continuing pipeline")

    runner = PipelineRunner(
        steps=[ProfileStep(), MatchStep(), GapStep(), PathStep(), AdviceStep()],
        fallback_handler=_fallback_handler,
    )

    queue = asyncio.Queue()

    async def on_progress(step_name, progress, message):
        await queue.put(("progress", step_name, progress, message))

    async def run_pipeline():
        state_out = await runner.run(state, on_progress=on_progress)
        # 在后台任务中保存诊断，使用全新的独立数据库 session 避免请求生命周期结束关闭
        async with async_session() as bg_db:
            diag = await _save_diagnosis(bg_db, student_id, state_out, diagnosis_type, trigger_event)
        await queue.put(("done", diag))

    asyncio.create_task(run_pipeline())

    async def event_generator():
        yield f"data: {json.dumps({'stage': 'start', 'progress': 0, 'message': '开始诊断...'}, ensure_ascii=False)}\n\n"

        diag = None
        while True:
            msg = await queue.get()
            if msg[0] == "done":
                diag = msg[1]
                break
            _, step_name, progress, message = msg
            yield f"data: {json.dumps({'stage': step_name, 'progress': round(progress, 2), 'message': message}, ensure_ascii=False)}\n\n"

        result_data = diag.model_dump()
        result_data["stage"] = "result"
        yield f"data: {json.dumps(result_data, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# 全量初步诊断，通过 SSE 流式返回分析进度和结果
@router.post("/full")
async def full_diagnosis(req: DiagnoseRequest, db: AsyncSession = Depends(get_db)):
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise HTTPException(503, "AI服务未就绪，请在后端配置 LLM_API_KEY 环境变量")
    return await _run_pipeline_sse(req.student_id, db, "initial", "")


# 基于技能变化触发的再诊断
@router.post("/re-evaluate")
async def re_evaluate(req: ReEvaluateRequest, db: AsyncSession = Depends(get_db)):
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise HTTPException(503, "AI服务未就绪，请在后端配置 LLM_API_KEY 环境变量")
    return await _run_pipeline_sse(req.student_id, db, "re_evaluation", req.trigger_event)


# 获取学生的诊断历史记录列表
@router.get("/history/{student_id}")
async def diagnosis_history(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiagORM).where(DiagORM.student_id == student_id).order_by(DiagORM.created_at.desc()))
    records = result.scalars().all()
    items = []
    for r in records:
        try:
            items.append(DiagnosisResponse(
                id=r.id, student_id=r.student_id, version=r.version,
                diagnosis_type=r.diagnosis_type, match_score=r.match_score or 0,
                dimension_scores=r.dimension_scores or {},
                dimension_changes=r.dimension_changes or {},
                gap_details=r.gap_details or [],
                top5_jobs=r.top5_jobs or [],
                growth_path=r.growth_path or {},
                career_advice=r.career_advice or "",
                ai_reasoning=r.ai_reasoning or {},
                trigger_event=r.trigger_event or "",
                created_at=r.created_at.isoformat() if r.created_at else None,
            ).model_dump())
        except Exception:
            items.append({"id": r.id, "error": "data corrupted", "version": r.version})
    return items


# 获取单条诊断记录详情
@router.get("/{diagnosis_id}")
async def get_diagnosis(diagnosis_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiagORM).where(DiagORM.id == diagnosis_id))
    r = result.scalar_one_or_none()
    if not r:
        return {"error": "Not found"}
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
            trigger_event=r.trigger_event or "",
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
    except Exception:
        return {"id": r.id, "error": "data corrupted", "version": r.version}
