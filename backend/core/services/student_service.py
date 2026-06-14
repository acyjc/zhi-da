# 学生管理服务——创建、查询、更新学生及技能水平
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Student as StudentORM, GrowthRecord
from core.models.student import StudentCreate, StudentUpdate, StudentResponse, SkillUpdateRequest


def _compute_completeness(student: StudentORM) -> float:
    """计算档案完整度（0-100）。"""
    score = 0.0
    total = 0.0

    # 必填字段（60分）
    required = {
        'name': 10, 'grade': 8, 'education_level': 8,
        'school': 8, 'major': 8, 'target_job': 10,
    }
    for field, weight in required.items():
        total += weight
        val = getattr(student, field, None)
        if val and str(val).strip():
            score += weight

    # 检查 profile_sections 中的技能与经历
    ps = student.profile_sections or {}
    total += 8
    if isinstance(ps, dict):
        skills = ps.get('skills', [])
        if skills and len(skills) >= 1:
            score += 8

    total += 10
    if isinstance(ps, dict):
        proj = ps.get('project_exp', [])
        intern = ps.get('internship_exp', [])
        if (proj and len(proj) >= 1) or (intern and len(intern) >= 1):
            score += 10
    else:
        # 兼容旧字段
        if student.project_exp and len(student.project_exp) >= 1:
            score += 10

    # 推荐字段（28分）
    recommended = {
        'phone': 2, 'email': 2, 'self_evaluation': 3,
    }
    for field, weight in recommended.items():
        total += weight
        val = getattr(student, field, None)
        if val and str(val).strip():
            score += weight

    if isinstance(ps, dict):
        # 教育经历扩展
        total += 3
        edu = ps.get('education')
        if edu and (edu.get('rank_description') or edu.get('english_level')):
            score += 3
        # 求职意向
        total += 3
        ji = ps.get('job_intention')
        if ji and (ji.get('expected_industry') or ji.get('job_type')):
            score += 3
        # 实习经历
        total += 4
        if ps.get('internship_exp') and len(ps['internship_exp']) >= 1:
            score += 4
        # 奖励荣誉
        total += 3
        if ps.get('awards') and len(ps['awards']) >= 1:
            score += 3
        # 论文/专利
        total += 2
        if ps.get('publications') and len(ps['publications']) >= 1:
            score += 2
        # 社会实践
        total += 2
        if ps.get('campus_exp') and len(ps['campus_exp']) >= 1:
            score += 2

    return round(min(score / total * 100, 100), 1) if total > 0 else 0.0


def _serialize_profile_sections(ps) -> dict | None:
    """将 profile_sections 从 ORM 或 Pydantic 对象序列化为 dict。"""
    if ps is None:
        return None
    if isinstance(ps, dict):
        return ps
    if hasattr(ps, 'model_dump'):
        return ps.model_dump()
    return ps


async def create_student(db: AsyncSession, data: StudentCreate) -> StudentResponse:
    ps_dict = data.profile_sections.model_dump() if data.profile_sections else {}
    student = StudentORM(
        name=data.name, grade=data.grade, major=data.major,
        target_job=data.target_job, tech_skills=data.tech_skills,
        project_exp=[p.model_dump() for p in data.project_exp],
        soft_skills=data.soft_skills, domain_knowledge=data.domain_knowledge,
        resume_text=data.resume_text,
        academic_foundation=data.academic_foundation.model_dump() if data.academic_foundation else {},
        soft_skill_evidence={k: v.model_dump() for k, v in data.soft_skill_evidence.items()} if data.soft_skill_evidence else {},
        school=data.school, education_level=data.education_level,
        phone=data.phone, email=data.email,
        self_evaluation=data.self_evaluation,
        profile_sections=ps_dict,
    )
    student.profile_completeness = _compute_completeness(student)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


async def get_student(db: AsyncSession, student_id: int) -> StudentResponse | None:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    return StudentResponse.model_validate(student) if student else None


async def update_student(db: AsyncSession, student_id: int, data: StudentUpdate) -> StudentResponse | None:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return None
    update_data = data.model_dump(exclude_unset=True)
    # 特殊处理 profile_sections
    if 'profile_sections' in update_data and update_data['profile_sections'] is not None:
        ps_val = update_data['profile_sections']
        if hasattr(ps_val, 'model_dump'):
            update_data['profile_sections'] = ps_val.model_dump()
    for key, value in update_data.items():
        setattr(student, key, value)
    student.profile_completeness = _compute_completeness(student)
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


# 手动更新技能，对比前后差异并写入成长记录
async def update_skills(db: AsyncSession, student_id: int, data: SkillUpdateRequest) -> dict:
    result = await db.execute(select(StudentORM).where(StudentORM.id == student_id))
    student = result.scalar_one_or_none()
    if not student:
        return {"success": False, "error": "Student not found"}

    before_snapshot = {
        "tech_skills": dict(student.tech_skills or {}),
        "soft_skills": dict(student.soft_skills or {}),
        "domain_knowledge": dict(student.domain_knowledge or {}),
        "project_exp": list(student.project_exp or []),
        "academic_foundation": dict(student.academic_foundation or {}),
        "soft_skill_evidence": dict(student.soft_skill_evidence or {}),
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

    if data.academic_foundation is not None:
        student.academic_foundation = data.academic_foundation.model_dump()
        changes.append("更新了学业基础")

    if data.soft_skill_evidence is not None:
        student.soft_skill_evidence = {k: v.model_dump() for k, v in data.soft_skill_evidence.items()}
        changes.append("更新了软技能证据")

    after_snapshot = {
        "tech_skills": dict(student.tech_skills or {}),
        "soft_skills": dict(student.soft_skills or {}),
        "domain_knowledge": dict(student.domain_knowledge or {}),
        "project_exp": list(student.project_exp or []),
        "academic_foundation": dict(student.academic_foundation or {}),
        "soft_skill_evidence": dict(student.soft_skill_evidence or {}),
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
