# 任务进度路由——标记任务完成(触发技能更新)、查询进度列表
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import TaskProgress as TaskORM, Student as StudentORM, GrowthRecord
from core.models.progress import TaskCompleteRequest, TaskProgressResponse

router = APIRouter(prefix="/api/progress", tags=["progress"])


# 标记任务完成，自动更新技能值并写入成长记录，返回是否需要再诊断
@router.post("/task-complete")
async def complete_task(req: TaskCompleteRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TaskORM).where(TaskORM.task_name == req.task_id, TaskORM.student_id == req.student_id))
    task = result.scalar_one_or_none()
    if not task:
        task = TaskORM(
            student_id=req.student_id,
            task_name=req.task_id,
            status="in_progress",
            skill_impact={},
        )
        db.add(task)
        await db.flush()

    student_result = await db.execute(select(StudentORM).where(StudentORM.id == req.student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        return {"success": False, "error": "Student not found"}

    before_snapshot = {"tech_skills": dict(student.tech_skills or {})}
    skill_impact = task.skill_impact or {}

    tech_skills = dict(student.tech_skills or {})
    for skill_name, impact_data in skill_impact.items():
        delta = impact_data.get("delta", 0) if isinstance(impact_data, dict) else impact_data
        current = tech_skills.get(skill_name, 0)
        tech_skills[skill_name] = min(100, max(0, current + delta))

    student.tech_skills = tech_skills
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    task.evidence = req.evidence

    record = GrowthRecord(
        student_id=req.student_id, record_type="task_completed",
        description=f"完成任务: {task.task_name}",
        before_snapshot=before_snapshot,
        after_snapshot={"tech_skills": tech_skills},
    )
    db.add(record)
    await db.commit()

    skill_updates = {}
    for skill_name, impact_data in skill_impact.items():
        delta = impact_data.get("delta", 0) if isinstance(impact_data, dict) else impact_data
        before_val = before_snapshot["tech_skills"].get(skill_name, 0)
        after_val = tech_skills.get(skill_name, 0)
        skill_updates[skill_name] = {"before": before_val, "after": after_val, "delta": delta}

    has_significant_change = any(abs(u["delta"]) >= 5 for u in skill_updates.values())

    return {
        "success": True,
        "skill_updates": skill_updates,
        "should_re_evaluate": has_significant_change,
        "diagnosis_suggested": "你的能力有显著提升，建议重新诊断以获得更精准的岗位匹配和路径规划" if has_significant_change else "",
    }


# 获取学生所有任务进度
@router.get("/{student_id}")
async def get_progress(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskORM).where(TaskORM.student_id == student_id).order_by(TaskORM.phase_index, TaskORM.task_index))
    tasks = result.scalars().all()
    return [TaskProgressResponse(
        id=t.id, student_id=t.student_id, diagnosis_id=t.diagnosis_id,
        phase_index=t.phase_index, task_index=t.task_index, task_name=t.task_name,
        status=t.status,
        completed_at=t.completed_at.isoformat() if t.completed_at else None,
        evidence=t.evidence, skill_impact=t.skill_impact or {},
    ).model_dump() for t in tasks]
