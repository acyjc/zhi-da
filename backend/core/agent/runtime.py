# AgentRuntime——受控智能体运行时
# 从固定 LLM 工作流升级为受控智能体，支持上下文加载、工具调用、状态判断和记忆保存

from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from db.models import (
    Student, JobPost, Enterprise, DiagnosisResult, JobAbilityModel,
    TaskProgress, GrowthRecord, GrowthTask, StudentAuthorization
)


# ---- 上下文加载器 ----
class ContextLoader:
    """加载学生、岗位、企业、历史诊断、成长任务等业务上下文。"""

    @staticmethod
    async def load_student(db: AsyncSession, student_id: int) -> Optional[dict]:
        student = await db.get(Student, student_id)
        if not student:
            return None
        return {
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "major": student.major,
            "target_job": student.target_job,
            "tech_skills": student.tech_skills or {},
            "project_exp": student.project_exp or [],
            "soft_skills": student.soft_skills or {},
            "domain_knowledge": student.domain_knowledge or {},
            "resume_text": student.resume_text or "",
            "academic_foundation": student.academic_foundation or {},
            "soft_skill_evidence": student.soft_skill_evidence or {},
            # 新字段（profile_sections 模块化结构）
            "school": student.school or "",
            "education_level": student.education_level or "",
            "phone": student.phone or "",
            "email": student.email or "",
            "self_evaluation": student.self_evaluation or "",
            "profile_completeness": student.profile_completeness or 0.0,
            "profile_sections": student.profile_sections or {},
        }

    @staticmethod
    async def get_active_jobs(db: AsyncSession) -> list[dict]:
        """获取所有 active 企业的 approved 岗位"""
        stmt = (
            select(JobPost, Enterprise.name.label("enterprise_name"))
            .join(Enterprise, JobPost.enterprise_id == Enterprise.id)
            .where(
                JobPost.status == "approved",
                Enterprise.status == "active"
            )
            .order_by(JobPost.created_at.desc())
        )
        result = await db.execute(stmt)
        jobs = []
        for row in result.all():
            job = row[0]
            jobs.append({
                "id": job.id,
                "title": job.title,
                "category": job.category,
                "enterprise_name": row.enterprise_name,
                "enterprise_id": job.enterprise_id,
            })
        return jobs

    @staticmethod
    async def get_job_ability_model(db: AsyncSession, job_id: str) -> Optional[dict]:
        stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None
        return {
            "tech_skills": model.tech_skills or {},
            "soft_skills": model.soft_skills or {},
            "domain_knowledge": model.domain_knowledge or {},
            "project_exp": model.project_exp or [],
            "weight_config": model.weight_config or {},
        }

    @staticmethod
    async def get_diagnosis_history(db: AsyncSession, student_id: int, limit: int = 5) -> list[dict]:
        stmt = (
            select(DiagnosisResult)
            .where(DiagnosisResult.student_id == student_id)
            .order_by(desc(DiagnosisResult.version))
            .limit(limit)
        )
        result = await db.execute(stmt)
        records = result.scalars().all()
        return [{
            "version": r.version,
            "diagnosis_type": r.diagnosis_type,
            "match_score": r.match_score,
            "dimension_scores": r.dimension_scores or {},
            "dimension_changes": r.dimension_changes or {},
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "ai_status": r.ai_status or "available",
        } for r in records]

    @staticmethod
    async def get_growth_progress(db: AsyncSession, student_id: int) -> dict:
        """获取学生的成长任务进度"""
        # 新版 GrowthTask
        stmt_new = select(GrowthTask).where(GrowthTask.student_id == student_id).order_by(GrowthTask.phase_index, GrowthTask.task_index)
        result_new = await db.execute(stmt_new)
        new_tasks = result_new.scalars().all()

        # 旧版 TaskProgress
        stmt_old = select(TaskProgress).where(TaskProgress.student_id == student_id).order_by(TaskProgress.phase_index, TaskProgress.task_index)
        result_old = await db.execute(stmt_old)
        old_tasks = result_old.scalars().all()

        completed = sum(1 for t in new_tasks if t.status == "completed") + sum(1 for t in old_tasks if t.status == "completed")
        total = len(new_tasks) + len(old_tasks)

        return {
            "growth_tasks": [{
                "id": t.id,
                "task_name": t.task_name,
                "status": t.status,
                "linked_gap": t.linked_gap,
                "target_dimension": t.target_dimension,
                "expected_impact": t.expected_impact,
            } for t in new_tasks],
            "legacy_tasks": [{
                "id": t.id,
                "task_name": t.task_name,
                "status": t.status,
            } for t in old_tasks],
            "completed_count": completed,
            "total_count": total,
        }

    @staticmethod
    async def get_student_authorizations(db: AsyncSession, student_id: int) -> list[dict]:
        stmt = (
            select(StudentAuthorization, JobPost.title.label("job_title"), Enterprise.name.label("ent_name"))
            .join(JobPost, StudentAuthorization.job_post_id == JobPost.id)
            .join(Enterprise, StudentAuthorization.enterprise_id == Enterprise.id)
            .where(StudentAuthorization.student_id == student_id, StudentAuthorization.status == "active")
        )
        result = await db.execute(stmt)
        auths = []
        for row in result.all():
            auth = row[0]
            auths.append({
                "id": auth.id,
                "job_title": row.job_title,
                "enterprise_name": row.ent_name,
                "diagnosis_id": auth.diagnosis_id,
            })
        return auths

    @staticmethod
    async def check_info_completeness(student: dict) -> dict:
        """检查学生信息完整度，返回缺失字段列表。

        优先检查 profile_sections（新结构），回退到旧字段兼容。
        """
        missing = []
        ps = student.get("profile_sections") or {}

        # 技能：优先 profile_sections.skills，回退到 tech_skills
        skills = ps.get("skills", [])
        old_skills = student.get("tech_skills", {})
        if not skills and not old_skills:
            missing.append("tech_skills")

        # 项目/实习经历：优先 profile_sections 数组，回退到旧 project_exp
        ps_projects = ps.get("project_exp", [])
        ps_internships = ps.get("internship_exp", [])
        old_projects = student.get("project_exp", [])
        if not ps_projects and not ps_internships and not old_projects:
            missing.append("project_exp")

        # 学业基础
        if not student.get("academic_foundation") or not student.get("academic_foundation", {}).get("gpa"):
            missing.append("academic_foundation")

        # 软技能证据
        if not student.get("soft_skill_evidence"):
            missing.append("soft_skill_evidence")

        # 目标岗位
        if not student.get("target_job"):
            missing.append("target_job")

        # 简历文本（可选但推荐）
        if not student.get("resume_text"):
            missing.append("resume_text")

        return {
            "is_complete": len(missing) <= 2,  # 缺 2 项以内视为完整
            "missing_fields": missing,
            "completeness": round(1 - len(missing) / 6, 2),
        }


# ---- 规划器（Legacy） ----
# Legacy: kept for backward compatibility and old tests.
# New code should use core.agent.planner.StudentPlanner.
class Planner:
    """判断当前应该执行什么操作：完整诊断、补充追问、复评、任务生成。

    Legacy: 新代码请使用 core.agent.planner.StudentPlanner。
    此类仅保留用于旧测试兼容。
    """

    @staticmethod
    async def plan(db: AsyncSession, student_id: int) -> dict:
        student = await ContextLoader.load_student(db, student_id)
        if not student:
            return {"action": "error", "reason": "学生不存在"}

        completeness = await ContextLoader.check_info_completeness(student)
        history = await ContextLoader.get_diagnosis_history(db, student_id, limit=3)
        progress = await ContextLoader.get_growth_progress(db, student_id)

        # 判断逻辑
        if not completeness["is_complete"]:
            return {
                "action": "ask_for_info",
                "missing_fields": completeness["missing_fields"],
                "completeness": completeness["completeness"],
                "reason": f"学生信息完整度仅 {completeness['completeness']:.0%}，需要补充关键信息",
            }

        if not history:
            return {
                "action": "initial_diagnosis",
                "reason": "学生信息完整且无诊断历史，执行初诊",
            }

        latest = history[0]
        completed_tasks = progress["completed_count"]

        # 如果有新完成的任务且未触发复评
        if completed_tasks > 0 and latest["diagnosis_type"] != "task_re_evaluation":
            return {
                "action": "re_evaluation",
                "trigger": "task_completion",
                "reason": f"已完成 {completed_tasks} 个成长任务，建议触发复评",
                "latest_version": latest["version"],
            }

        return {
            "action": "plan_or_chat",
            "reason": "信息完整且已有诊断，可以规划或对话",
            "latest_version": latest["version"],
            "latest_match_score": latest.get("match_score", 0),
        }


# ---- 输出校验器 ----
class OutputValidator:
    """校验 AI 输出的 JSON 结构、分数范围和字段完整性。"""

    @staticmethod
    def validate_dimension_scores(scores: dict) -> dict:
        """确保所有维度分数在 0-1 范围内"""
        validated = {}
        for key in ["tech_skills", "project_exp", "academic_foundation", "domain_knowledge", "soft_skill_evidence"]:
            val = scores.get(key, 0)
            try:
                val = max(0.0, min(1.0, float(val)))
            except (TypeError, ValueError):
                val = 0.0
            validated[key] = round(val, 3)
        return validated

    @staticmethod
    def validate_match_score(score) -> float:
        try:
            return round(max(0.0, min(1.0, float(score))), 3)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def validate_top5_jobs(jobs: list) -> list:
        validated = []
        for job in (jobs or []):
            if not isinstance(job, dict):
                continue
            score = job.get("match_score", job.get("score", 0))
            try:
                score = max(0.0, min(1.0, float(score)))
            except (TypeError, ValueError):
                score = 0.0
            validated.append({
                "job_id": str(job.get("job_id", "")),
                "title": str(job.get("title", "")),
                "match_score": round(score, 3),
                "company": str(job.get("company", "")),
                "reason": str(job.get("reason", "")),
                "matched_skills": list(job.get("matched_skills", [])),
                "missing_skills": list(job.get("missing_skills", [])),
            })
        return validated[:5]


# ---- 记忆写入器（Legacy） ----
# Legacy: kept for backward compatibility and old tests.
# New code should use core.services.growth_task_service
# and core.services.diagnosis_service.
class MemoryWriter:
    """保存诊断结果、解释、任务摘要到数据库。

    Legacy: 新代码请使用 core.services.growth_task_service 和 core.services.diagnosis_service。
    save_growth_tasks() 已委托给 growth_task_service.create_from_growth_path()。
    """

    @staticmethod
    async def save_growth_tasks(db: AsyncSession, student_id: int, diagnosis_id: str, tasks: dict):
        """将成长任务保存到 GrowthTask 表。

        Legacy: 内部已委托给 growth_task_service.create_from_growth_path()。

        tasks 结构示例：{"phases": [{"tasks": [...]}, ...]}
        防重复：同一 diagnosis_id 已有任务则跳过。
        """
        from core.services import growth_task_service
        growth_path = tasks if isinstance(tasks, dict) else {}
        return await growth_task_service.create_from_growth_path(
            db, student_id, diagnosis_id, growth_path
        )

    @staticmethod
    async def create_diagnosis_summary(db: AsyncSession, student_id: int, action: str, details: dict):
        """创建诊断摘要记录（用于对话历史）"""
        # 这里暂时使用 GrowthRecord 来记录，未来可以迁移到专用表
        record = GrowthRecord(
            student_id=student_id,
            record_type="agent_action",
            description=f"Agent action: {action} - {details.get('reason', '')}",
            before_snapshot=details,
            after_snapshot={"action": action},
        )
        db.add(record)
        await db.commit()
        return record


# ---- 解释构建器 ----
class ExplanationBuilder:
    """生成统一解释结构。"""

    @staticmethod
    def build_followup_questions(missing_fields: list) -> list[dict]:
        """根据缺失字段生成补充问题"""
        question_map = {
            "resume_text": {
                "question": "你还没有上传简历，可以上传简历或者粘贴你的个人简介吗？",
                "field": "resume_text",
                "priority": "high",
            },
            "tech_skills": {
                "question": "你掌握了哪些技能？例如编程语言、框架、工具、语言能力等。请在「技能/爱好」模块中添加。",
                "field": "tech_skills",
                "priority": "high",
            },
            "project_exp": {
                "question": "你参与过哪些项目或实习经历？请在「项目经验」或「实习经历」模块中补充，包括项目名称、你的角色和主要贡献。",
                "field": "project_exp",
                "priority": "high",
            },
            "academic_foundation": {
                "question": "你的学业情况如何？包括成绩排名、核心课程和获奖情况。请在「教育经历」中补充。",
                "field": "academic_foundation",
                "priority": "medium",
            },
            "soft_skill_evidence": {
                "question": "你在团队协作、沟通表达、主动性方面有哪些具体经历可以分享？",
                "field": "soft_skill_evidence",
                "priority": "medium",
            },
            "target_job": {
                "question": "你的目标岗位方向是什么？例如后端开发、前端开发、数据分析、产品经理等。请在「求职意向」中设置。",
                "field": "target_job",
                "priority": "high",
            },
        }
        questions = []
        for field in missing_fields:
            if field in question_map:
                questions.append(question_map[field])
        return questions
