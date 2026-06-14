# 诊断服务——统一管理诊断结果的保存、版本递增、快照构建和 GrowthTask 自动落库
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from db.models import DiagnosisResult as DiagORM
from config.settings import LLM_API_KEY, LLM_MODEL
from core.models.diagnosis import DiagnosisResponse
from core.harness.step import PipelineState

logger = logging.getLogger(__name__)

# 智能体版本常量（统一管理，供 route 和 agent runtime 引用）
AGENT_VERSION = "2.0"
PROMPT_VERSION = "v1"


def compute_dimension_changes(current: dict, previous: dict) -> dict:
    """计算两个维度分数之间的变化量。"""
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


def normalize_top5_jobs(top5_jobs: list) -> list:
    """统一 top5_jobs 字段中的分数字段，确保每个岗位都有 match_score 字段。"""
    normalized = []
    for job in top5_jobs:
        if not isinstance(job, dict):
            continue
        score = job.get("match_score", job.get("score", 0))
        try:
            score = max(0.0, min(1.0, float(score)))
        except (TypeError, ValueError):
            score = 0.0
        matched = job.get("matched_skills", [])
        missing = job.get("missing_skills", [])
        normalized.append({
            "job_id": job.get("job_id", ""),
            "title": job.get("title", ""),
            "match_score": round(score, 3),
            "company": job.get("company", ""),
            "reason": job.get("reason", ""),
            "matched_skills": matched if isinstance(matched, list) else [],
            "missing_skills": missing if isinstance(missing, list) else [],
            "confidence": job.get("confidence", 0.7),
        })
    return normalized


def _build_input_snapshot(student_input: dict) -> dict:
    """构建诊断时的学生输入快照。"""
    return {
        "student_id": student_input.get("id", ""),
        "name": student_input.get("name", ""),
        "grade": student_input.get("grade", ""),
        "major": student_input.get("major", ""),
        "target_job": student_input.get("target_job", ""),
        "tech_skills": student_input.get("tech_skills", {}),
        "project_exp_count": len(student_input.get("project_exp", [])),
        "has_resume": bool(student_input.get("resume_text")),
        "has_academic": bool(student_input.get("academic_foundation")),
        "has_soft_evidence": bool(student_input.get("soft_skill_evidence")),
    }


def _determine_ai_status(state: PipelineState) -> str:
    """根据 pipeline 状态和配置判断 AI 状态。"""
    has_errors = len(state.errors) > 0 if hasattr(state, "errors") else False
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        return "missing_key"
    if has_errors:
        return "fallback_rule_based"
    return "available"


def _build_diagnosis_response(diag: DiagORM, ai_status: str = "available") -> DiagnosisResponse:
    """从 ORM 对象安全构建 DiagnosisResponse。"""
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
            ability_profile=diag.ability_profile or {},
            explanations=diag.explanations or {},
            confidence=diag.confidence or {},
            ai_status=diag.ai_status or ai_status,
            trigger_event=diag.trigger_event or "",
            created_at=diag.created_at.isoformat() if diag.created_at else None,
        )
    except Exception:
        return DiagnosisResponse(
            id=diag.id, student_id=diag.student_id, version=diag.version,
            diagnosis_type=diag.diagnosis_type, match_score=diag.match_score or 0,
            dimension_scores={}, dimension_changes={}, gap_details=[],
            top5_jobs=[], growth_path={}, career_advice="",
            ai_reasoning={}, ability_profile={}, explanations={},
            confidence={}, ai_status=ai_status,
            trigger_event=diag.trigger_event or "",
            created_at=diag.created_at.isoformat() if diag.created_at else None,
        )


async def save_diagnosis(
    db: AsyncSession,
    student_id: int,
    state: PipelineState,
    diagnosis_type: str = "initial",
    trigger_event: str = "",
) -> DiagnosisResponse:
    """保存诊断结果到数据库，自动递增版本号并落库 GrowthTask。

    此函数从 diagnosis route 的 _save_diagnosis 迁移而来，
    可被 route 和 AgentRuntime 共同复用。

    版本号递增使用重试机制防止并发冲突。
    """
    match_result = dict(state.get("match_result", {}))
    match_result.setdefault("previous_dimension_scores", state.extra.get("previous_dimension_scores", {}))

    # 统一 top5_jobs
    raw_top5 = match_result.get("top5_jobs", [])
    normalized_top5 = normalize_top5_jobs(raw_top5)

    # 输入快照
    student_input = dict(state.input)
    input_snapshot = _build_input_snapshot(student_input)

    # AI 状态
    ai_status = _determine_ai_status(state)

    # 版本递增——带重试的原子操作
    version = None
    for attempt in range(3):
        result = await db.execute(
            select(func.max(DiagORM.version)).where(DiagORM.student_id == student_id)
        )
        max_ver = result.scalar() or 0
        version = max_ver + 1

        # 检查是否已有相同版本（并发冲突检测）
        existing = await db.execute(
            select(DiagORM).where(
                DiagORM.student_id == student_id,
                DiagORM.version == version,
            )
        )
        if existing.scalar_one_or_none() is None:
            break
        # 冲突：等待短暂时间后重试
        import asyncio
        await asyncio.sleep(0.05)
    else:
        # 3 次重试仍冲突，强制使用更高版本号
        version = (max_ver or 0) + attempt + 2

    diag = DiagORM(
        student_id=student_id,
        version=version,
        diagnosis_type=diagnosis_type,
        match_score=match_result.get("match_score", 0),
        dimension_scores=match_result.get("dimension_scores", {}),
        dimension_changes=compute_dimension_changes(
            match_result.get("dimension_scores", {}),
            match_result.get("previous_dimension_scores", {}),
        ),
        gap_details=match_result.get("gap_details", []),
        top5_jobs=normalized_top5,
        growth_path=state.get("growth_path", {}),
        career_advice=state.get("career_advice", ""),
        ai_reasoning=state.get("ai_reasoning", {}),
        ability_profile=state.get("profile", {}),
        explanations=state.get("explanations", {}),
        confidence=state.get("confidence", {}),
        input_snapshot=input_snapshot,
        job_snapshot=state.extra.get("job_snapshot", []),
        model_name=LLM_MODEL,
        prompt_version=PROMPT_VERSION,
        agent_version=AGENT_VERSION,
        ai_status=ai_status,
        trigger_event=trigger_event,
    )
    db.add(diag)
    await db.commit()
    await db.refresh(diag)

    # 自动将成长任务写入 GrowthTask 表（委托给 growth_task_service）
    growth_path = diag.growth_path or {}
    if growth_path.get("phases"):
        try:
            from core.services.growth_task_service import create_from_growth_path
            await create_from_growth_path(db, student_id, diag.id, growth_path)
        except Exception as exc:
            logger.warning(
                "GrowthTask 落库失败 (diagnosis_id=%s, student_id=%s): %s",
                diag.id, student_id, exc, exc_info=True,
            )

    return _build_diagnosis_response(diag, ai_status)


async def get_latest_diagnosis(db: AsyncSession, student_id: int) -> DiagORM | None:
    """获取学生最新一条诊断记录。"""
    result = await db.execute(
        select(DiagORM)
        .where(DiagORM.student_id == student_id)
        .order_by(DiagORM.version.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_diagnosis_by_id(db: AsyncSession, diagnosis_id: str) -> DiagORM | None:
    """按 ID 获取单条诊断记录。"""
    return await db.get(DiagORM, diagnosis_id)


async def list_diagnosis_history(db: AsyncSession, student_id: int) -> list[dict]:
    """获取学生全部诊断历史（按时间倒序）。"""
    result = await db.execute(
        select(DiagORM)
        .where(DiagORM.student_id == student_id)
        .order_by(DiagORM.created_at.desc())
    )
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
                ability_profile=r.ability_profile or {},
                explanations=r.explanations or {},
                confidence=r.confidence or {},
                ai_status=r.ai_status or "available",
                trigger_event=r.trigger_event or "",
                created_at=r.created_at.isoformat() if r.created_at else None,
            ).model_dump())
        except Exception:
            items.append({"id": r.id, "error": "data corrupted", "version": r.version})
    return items
