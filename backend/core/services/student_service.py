# 学生管理服务——创建、查询、更新学生及技能水平
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Student as StudentORM, GrowthRecord
from core.models.student import StudentCreate, StudentUpdate, StudentResponse, SkillUpdateRequest


async def create_student(db: AsyncSession, data: StudentCreate) -> StudentResponse:
    student = StudentORM(
        name=data.name, grade=data.grade, major=data.major,
        target_job=data.target_job, tech_skills=data.tech_skills,
        project_exp=[p.model_dump() for p in data.project_exp],
        soft_skills=data.soft_skills, domain_knowledge=data.domain_knowledge,
        resume_text=data.resume_text,
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


async def get_student(db: AsyncSession, student_id: str) -> StudentResponse | None:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    return StudentResponse.model_validate(student) if student else None


async def update_student(db: AsyncSession, student_id: str, data: StudentUpdate) -> StudentResponse | None:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(student, key, value)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


# 手动更新技能，对比前后差异并写入成长记录
async def update_skills(db: AsyncSession, student_id: str, data: SkillUpdateRequest) -> dict:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {"success": False, "error": "Student not found"}

    before_snapshot = {
        "tech_skills": dict(student.tech_skills or {}),
        "soft_skills": dict(student.soft_skills or {}),
        "domain_knowledge": dict(student.domain_knowledge or {}),
        "project_exp": list(student.project_exp or []),
    }

    changes = []
    if data.tech_skills is not None:
        old = dict(student.tech_skills or {})
        student.tech_skills = data.tech_skills
        changes.extend(_diff_skills(old, data.tech_skills, "tech_skills"))

    if data.soft_skills is not None:
        old = dict(student.soft_skills or {})
        student.soft_skills = data.soft_skills
        changes.extend(_diff_skills(old, data.soft_skills, "soft_skills"))

    if data.domain_knowledge is not None:
        old = dict(student.domain_knowledge or {})
        student.domain_knowledge = data.domain_knowledge
        changes.extend(_diff_skills(old, data.domain_knowledge, "domain_knowledge"))

    if data.project_exp is not None:
        old = list(student.project_exp or [])
        student.project_exp = [p.model_dump() for p in data.project_exp]
        changes.append("更新了项目经验")

    after_snapshot = {
        "tech_skills": dict(student.tech_skills or {}),
        "soft_skills": dict(student.soft_skills or {}),
        "domain_knowledge": dict(student.domain_knowledge or {}),
        "project_exp": list(student.project_exp or []),
    }

    record = GrowthRecord(
        student_id=student_id, record_type="skill_change",
        description=f"手动更新技能: {', '.join(changes) if changes else '无变化'}",
        before_snapshot=before_snapshot, after_snapshot=after_snapshot,
    )
    db.add(record)
    await db.commit()
    await db.refresh(student)

    has_change = len(changes) > 0
    return {
        "success": True,
        "changes": changes,
        "should_re_evaluate": has_change,
        "diagnosis_suggested": "你的技能水平已更新，建议重新诊断以获得最新的岗位匹配和路径规划" if has_change else "",
        "student": StudentResponse.model_validate(student).model_dump(),
    }


def _diff_skills(old: dict, new: dict, dimension: str) -> list[str]:
    diffs = []
    for key in set(old.keys()) | set(new.keys()):
        old_val = old.get(key, 0)
        new_val = new.get(key, 0)
        if old_val != new_val:
            diffs.append(f"{dimension}.{key}: {old_val}→{new_val}")
    return diffs
