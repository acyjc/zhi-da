# 企业端服务——企业信息管理、在招岗位发布、JD AI 模型解析、已授权候选人检索
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from core.utils.time import utc_now
from db.models import Enterprise, JobPost, JobAbilityModel, StudentAuthorization, Student, DiagnosisResult, StudentAttachment
from config.settings import LLM_API_KEY

SYSTEM_PROMPT = """你是一个专业的岗位JD（职业描述）分析助手。请严格按照以下JSON格式解析岗位JD，不要输出任何Markdown块或解释文字：
{
  "tech_skills": { "<技术技能名>": <推荐分值 0-100> },
  "soft_skills": { "<软技能名>": <推荐分值 0-100> },
  "domain_knowledge": { "<领域名>": <推荐分值 0-100> },
  "project_exp": [
    {
      "name": "<要求项目经验名称>",
      "description": "<1-2句话描述该项目经验的要求特征>"
    }
  ],
  "weight_config": {
    "tech_skills": <技术技能权重，0-1之间浮点数>,
    "project_exp": <项目经验权重，0-1之间浮点数>,
    "academic_foundation": <学业基础权重，0-1之间浮点数>,
    "domain_knowledge": <领域知识权重，0-1之间浮点数>,
    "soft_skill_evidence": <软技能证据权重，0-1之间浮点数>
  }
}

## 规则
1. 提取JD中明确或隐含的技术技能、项目经验、学业背景、软实力、领域知识要求。
2. 技能评分推荐分值通常在 60 到 90 之间（视JD中描述的重要程度而定）。
3. weight_config 中五项权重的加和必须等于 1.0。如果未明确提及，可使用默认权重 {"tech_skills": 0.35, "project_exp": 0.25, "academic_foundation": 0.10, "domain_knowledge": 0.15, "soft_skill_evidence": 0.15}。
4. 只返回上述纯JSON格式，禁止包裹在 ```json 或 ``` 块中。
"""

DEFAULT_WEIGHT_CONFIG = {
    "tech_skills": 0.35,
    "project_exp": 0.25,
    "academic_foundation": 0.10,
    "domain_knowledge": 0.15,
    "soft_skill_evidence": 0.15,
}


def _normalize_weight_config(raw: dict | None) -> dict:
    if not isinstance(raw, dict):
        raw = {}
    aliases = {
        "project": "project_exp",
        "academic": "academic_foundation",
        "domain": "domain_knowledge",
        "soft": "soft_skill_evidence",
        "soft_skills": "soft_skill_evidence",
    }
    weights = {}
    for key, default in DEFAULT_WEIGHT_CONFIG.items():
        raw_value = raw.get(key, default)
        for alias, target in aliases.items():
            if target == key and alias in raw:
                raw_value = raw[alias]
                break
        try:
            weights[key] = max(0.0, float(raw_value))
        except (TypeError, ValueError):
            weights[key] = default
    total = sum(weights.values())
    if total <= 0.01:
        return dict(DEFAULT_WEIGHT_CONFIG)
    return {key: round(value / total, 2) for key, value in weights.items()}


# 1. 获取企业资料
async def get_enterprise_profile(db: AsyncSession, ent_id: str):
    return await db.get(Enterprise, ent_id)


# 2. 更新企业资料
async def update_enterprise_profile(db: AsyncSession, ent_id: str, data: dict):
    ent = await db.get(Enterprise, ent_id)
    if not ent:
        # 自动初始化创建以防不存在
        ent = Enterprise(id=ent_id, name=data.get("name", "未命名企业"))
        db.add(ent)
        
    ent.name = data.get("name", ent.name)
    ent.industry = data.get("industry", ent.industry)
    ent.description = data.get("description", ent.description)
    ent.contact_name = data.get("contact_name", ent.contact_name)
    ent.contact_email = data.get("contact_email", ent.contact_email)
    ent.updated_at = utc_now()
    
    await db.commit()
    await db.refresh(ent)
    return ent


# 3. 获取在招岗位列表
async def list_enterprise_jobs(db: AsyncSession, ent_id: str):
    stmt = select(JobPost).where(JobPost.enterprise_id == ent_id).order_by(desc(JobPost.created_at))
    res = await db.execute(stmt)
    return res.scalars().all()


# 4. 创建在招岗位
async def create_enterprise_job(db: AsyncSession, ent_id: str, data: dict):
    # 状态默认为 draft 草稿，需 AI 解析能力模型后才可提交审核
    job = JobPost(
        enterprise_id=ent_id,
        title=data.get("title", "未命名岗位"),
        category=data.get("category", ""),
        description=data.get("description", ""),
        requirements_text=data.get("requirements_text", ""),
        status=data.get("status", "draft")
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


# 5. 更新在招岗位
async def update_enterprise_job(db: AsyncSession, ent_id: str, job_id: str, data: dict):
    job = await db.get(JobPost, job_id)
    if not job or job.enterprise_id != ent_id:
        return None
        
    job.title = data.get("title", job.title)
    job.category = data.get("category", job.category)
    job.description = data.get("description", job.description)
    job.requirements_text = data.get("requirements_text", job.requirements_text)
    if "status" in data:
        # 企业端不允许直接设为 approved，必须走审核流程
        new_status = data["status"]
        if new_status in ("draft", "pending_review"):
            job.status = new_status
        # 被驳回的岗位重新编辑后回到草稿态，清除旧的驳回原因
        if new_status == "draft" and job.review_reason:
            job.review_reason = ""
    job.updated_at = utc_now()
    
    await db.commit()
    await db.refresh(job)
    return job


# 6. AI 提取岗位能力模型 (JobAbilityAgent)
async def parse_job_ability_model(db: AsyncSession, job_id: str):
    job = await db.get(JobPost, job_id)
    if not job:
        return None

    # 调用大模型解析
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        # Fallback 模拟数据
        parsed = {
            "tech_skills": {"Python": 80, "FastAPI": 75},
            "soft_skills": {"团队协作": 75, "沟通表达": 70},
            "domain_knowledge": {"后端开发": 80},
            "project_exp": [{"name": "Web服务开发", "description": "使用Web框架开发过完整接口"}],
            "weight_config": dict(DEFAULT_WEIGHT_CONFIG)
        }
    else:
        from core.harness.llm import get_llm_client
        from api.routes.resume import _extract_json
        llm = get_llm_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"职位名称: {job.title}\n分类: {job.category}\n岗位描述及要求: {job.requirements_text}"}
        ]
        response = await llm.complete(messages)
        try:
            data = _extract_json(response.content)
            
            # 基础结构校验与清洗
            parsed = {
                "tech_skills": {},
                "soft_skills": {},
                "domain_knowledge": {},
                "project_exp": [],
                "weight_config": dict(DEFAULT_WEIGHT_CONFIG)
            }
            for f in ["tech_skills", "soft_skills", "domain_knowledge"]:
                val = data.get(f, {})
                if isinstance(val, dict):
                    parsed[f] = {str(k): max(0, min(100, int(v))) for k, v in val.items() if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit())}
            
            wc = data.get("weight_config", {})
            parsed["weight_config"] = _normalize_weight_config(wc)
                    
            proj = data.get("project_exp", [])
            if isinstance(proj, list):
                for p in proj:
                    if isinstance(p, dict) and "name" in p:
                        parsed["project_exp"].append({
                            "name": str(p["name"]),
                            "description": str(p.get("description", ""))
                        })
        except Exception as e:
            # 异常时使用兜底数据
            import logging
            logging.getLogger("enterprise.service").warning("JD解析异常，使用兜底: %s", e)
            parsed = {
                "tech_skills": {job.title: 70},
                "soft_skills": {"沟通表达": 60},
                "domain_knowledge": {job.category or "通用领域": 70},
                "project_exp": [],
                "weight_config": dict(DEFAULT_WEIGHT_CONFIG)
            }

    # 保存或更新到表
    stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()

    if model:
        model.tech_skills = parsed["tech_skills"]
        model.soft_skills = parsed["soft_skills"]
        model.domain_knowledge = parsed["domain_knowledge"]
        model.project_exp = parsed["project_exp"]
        model.weight_config = parsed["weight_config"]
        model.updated_at = utc_now()
    else:
        model = JobAbilityModel(
            job_post_id=job_id,
            tech_skills=parsed["tech_skills"],
            soft_skills=parsed["soft_skills"],
            domain_knowledge=parsed["domain_knowledge"],
            project_exp=parsed["project_exp"],
            weight_config=parsed["weight_config"]
        )
        db.add(model)

    await db.commit()
    await db.refresh(model)
    return model


# 7. 提交岗位审核（必须先完成 AI 能力模型解析）
async def submit_job_review(db: AsyncSession, ent_id: str, job_id: str):
    job = await db.get(JobPost, job_id)
    if not job or job.enterprise_id != ent_id:
        return None

    # 校验：只有已解析能力模型的岗位才能提交审核
    stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise ValueError("请先使用 AI 解析岗位能力模型后再提交审核")

    job.status = "pending_review"
    job.updated_at = utc_now()
    await db.commit()
    return job


# 8. 获取企业岗位的已授权候选人
async def list_authorized_candidates(db: AsyncSession, ent_id: str):
    # 查询所有授权状态为 active 且属于该企业的候选人记录
    stmt = (
        select(
            StudentAuthorization.id.label("auth_id"),
            StudentAuthorization.created_at.label("auth_date"),
            StudentAuthorization.status.label("auth_status"),
            Student.id.label("student_id"),
            Student.name.label("student_name"),
            Student.grade.label("student_grade"),
            Student.major.label("student_major"),
            JobPost.title.label("job_title"),
            JobPost.id.label("job_post_id"),
            DiagnosisResult.id.label("diagnosis_id"),
            DiagnosisResult.match_score.label("match_score"),
            DiagnosisResult.dimension_scores.label("dimension_scores")
        )
        .join(Student, StudentAuthorization.student_id == Student.id)
        .join(JobPost, StudentAuthorization.job_post_id == JobPost.id)
        .join(DiagnosisResult, StudentAuthorization.diagnosis_id == DiagnosisResult.id)
        .where(StudentAuthorization.enterprise_id == ent_id, StudentAuthorization.status == "active")
        .order_by(desc(DiagnosisResult.match_score))
    )
    result = await db.execute(stmt)
    candidates = []
    for row in result.all():
        candidates.append({
            "auth_id": row.auth_id,
            "auth_date": row.auth_date.isoformat() if row.auth_date else None,
            "student_id": row.student_id,
            "student_name": row.student_name,
            "student_grade": row.student_grade,
            "student_major": row.student_major,
            "job_title": row.job_title,
            "job_post_id": row.job_post_id,
            "diagnosis_id": row.diagnosis_id,
            "match_score": row.match_score,
            "dimension_scores": row.dimension_scores,
        })
    return candidates


# 9. 获取单个候选人授权详情
async def get_candidate_detail(db: AsyncSession, ent_id: str, student_id: int, auth_id: str):
    # 验证该授权是否有效且属于该企业
    auth = await db.get(StudentAuthorization, auth_id)
    if not auth or auth.enterprise_id != ent_id or auth.student_id != student_id or auth.status != "active":
        return None
        
    student = await db.get(Student, student_id)
    diag = await db.get(DiagnosisResult, auth.diagnosis_id)
    job_post = await db.get(JobPost, auth.job_post_id)
    
    if not student or not diag or not job_post:
        return None

    attachment_result = await db.execute(
        select(StudentAttachment)
        .where(StudentAttachment.student_id == student_id)
        .order_by(desc(StudentAttachment.uploaded_at))
    )
    attachments = [
        {
            "id": att.id,
            "category": att.category,
            "file_name": att.file_name,
            "file_type": att.file_type,
            "file_size": att.file_size,
            "uploaded_at": att.uploaded_at.isoformat() if att.uploaded_at else None,
            "visibility": att.visibility,
        }
        for att in attachment_result.scalars().all()
    ]
        
    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "grade": student.grade,
            "major": student.major,
            "school": student.school,
            "education_level": student.education_level,
            "phone": student.phone,
            "email": student.email,
            "target_job": student.target_job,
            "project_exp": student.project_exp or [],
            "profile_sections": student.profile_sections or {},
            "profile_completeness": student.profile_completeness or 0,
            "academic_foundation": student.academic_foundation or {},
            "soft_skill_evidence": student.soft_skill_evidence or {},
        },
        "job": {
            "id": job_post.id,
            "title": job_post.title,
            "description": job_post.description
        },
        "diagnosis": {
            "id": diag.id,
            "version": diag.version,
            "match_score": diag.match_score,
            "dimension_scores": diag.dimension_scores or {},
            "gap_details": diag.gap_details or [],
            "career_advice": diag.career_advice or "",
            "ai_reasoning": diag.ai_reasoning or {}
        },
        "authorization_time": auth.created_at.isoformat() if auth.created_at else None,
        "attachments": attachments,
    }
