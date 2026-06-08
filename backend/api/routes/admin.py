# 学校端管理后台路由——数据统计、学生列表、企业管理、岗位审核审核与驳回
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional, Literal
from db.database import get_db
from db.models import Student, Enterprise, JobPost, JobAbilityModel, StudentAuthorization, DiagnosisResult
from core.auth import require_admin, Identity

router = APIRouter(prefix="/api/admin", tags=["admin"])

# 默认分页常量
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class EnterpriseStatusUpdate(BaseModel):
    status: Literal["active", "disabled", "pending"]  # 仅允许三种合法状态


class EnterpriseCreate(BaseModel):
    name: str
    industry: Optional[str] = ""
    description: Optional[str] = ""
    contact_name: Optional[str] = ""
    contact_email: Optional[str] = ""
    status: Optional[Literal["active", "pending"]] = "active"


class JobAuditRequest(BaseModel):
    reason: str  # 驳回原因必填，不允许为空


# 1. 基础运营统计数据
@router.get("/summary")
async def get_summary(
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    student_count = await db.scalar(select(func.count(Student.id)))
    enterprise_count = await db.scalar(select(func.count(Enterprise.id)))
    job_count = await db.scalar(select(func.count(JobPost.id)))
    pending_job_count = await db.scalar(select(func.count(JobPost.id)).where(JobPost.status == "pending_review"))
    active_auth_count = await db.scalar(select(func.count(StudentAuthorization.id)).where(StudentAuthorization.status == "active"))

    return {
        "total_students": student_count or 0,
        "total_enterprises": enterprise_count or 0,
        "total_jobs": job_count or 0,
        "pending_jobs": pending_job_count or 0,
        "active_authorizations": active_auth_count or 0
    }


# 2. 获取学生列表（聚合查询 + 分页，消除 N+1）
@router.get("/students")
async def list_students(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    # CTE: 聚合每个学生的诊断次数和最新版本号
    diag_agg = (
        select(
            DiagnosisResult.student_id,
            func.count(DiagnosisResult.id).label("diag_count"),
            func.max(DiagnosisResult.version).label("max_version"),
        )
        .group_by(DiagnosisResult.student_id)
        .cte("diag_agg")
    )

    # 主查询: 左连接聚合结果 + 左连接最新诊断记录获取 match_score
    stmt = (
        select(
            Student,
            diag_agg.diag_count,
            DiagnosisResult.match_score.label("latest_score"),
        )
        .outerjoin(diag_agg, Student.id == diag_agg.student_id)
        .outerjoin(
            DiagnosisResult,
            (DiagnosisResult.student_id == Student.id)
            & (DiagnosisResult.version == diag_agg.max_version),
        )
        .order_by(Student.created_at.desc())
    )

    # 总数
    total = await db.scalar(select(func.count(Student.id))) or 0

    # 分页
    offset = (page - 1) * page_size
    res = await db.execute(stmt.offset(offset).limit(page_size))
    rows = res.all()

    # 格式化输出
    items = []
    for row in rows:
        student = row[0]
        diag_count = row[1] or 0
        latest_score = row[2]
        items.append(
            {
                "id": student.id,
                "name": student.name,
                "grade": student.grade,
                "major": student.major,
                "target_job": student.target_job,
                "created_at": student.created_at.isoformat() if student.created_at else None,
                "diagnosis_count": diag_count,
                "latest_score": latest_score,
            }
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# 3. 获取特定学生诊断及授权详情
@router.get("/students/{student_id}")
async def get_student_detail(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
        
    diag_stmt = select(DiagnosisResult).where(DiagnosisResult.student_id == student_id).order_by(desc(DiagnosisResult.version))
    diag_res = await db.execute(diag_stmt)
    diags = diag_res.scalars().all()
    
    auth_stmt = (
        select(StudentAuthorization, JobPost.title, Enterprise.name)
        .join(JobPost, StudentAuthorization.job_post_id == JobPost.id)
        .join(Enterprise, StudentAuthorization.enterprise_id == Enterprise.id)
        .where(StudentAuthorization.student_id == student_id)
    )
    auth_res = await db.execute(auth_stmt)
    auths = [{
        "id": row[0].id,
        "job_title": row[1],
        "enterprise_name": row[2],
        "status": row[0].status,
        "created_at": row[0].created_at.isoformat() if row[0].created_at else None
    } for row in auth_res.all()]
    
    return {
        "student": student,
        "diagnoses": diags,
        "authorizations": auths
    }


# 4. 获取合作企业列表（分页）
@router.get("/enterprises")
async def list_enterprises(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    total = await db.scalar(select(func.count(Enterprise.id))) or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    offset = (page - 1) * page_size
    stmt = select(Enterprise).order_by(Enterprise.created_at.desc()).offset(offset).limit(page_size)
    res = await db.execute(stmt)
    rows = res.scalars().all()

    items = []
    for ent in rows:
        items.append({
            "id": ent.id,
            "name": ent.name,
            "industry": ent.industry,
            "description": ent.description,
            "contact_name": ent.contact_name,
            "contact_email": ent.contact_email,
            "status": ent.status,
            "created_at": ent.created_at.isoformat() if ent.created_at else None,
            "updated_at": ent.updated_at.isoformat() if ent.updated_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# 5. 获取企业详情
@router.get("/enterprises/{enterprise_id}")
async def get_enterprise(
    enterprise_id: str,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    ent = await db.get(Enterprise, enterprise_id)
    if not ent:
        raise HTTPException(404, "Enterprise not found")
    return ent


# 5.1 新增企业（管理员创建）
@router.post("/enterprises")
async def create_enterprise(
    req: EnterpriseCreate,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    # 校验企业名称必填
    name = req.name.strip()
    if not name:
        raise HTTPException(400, "企业名称不能为空")

    # 校验企业名称不重复
    existing = await db.scalar(select(Enterprise).where(Enterprise.name == name))
    if existing:
        raise HTTPException(409, f"企业「{name}」已存在，请勿重复添加")

    # 校验状态值
    status = req.status or "active"
    if status not in ("active", "pending"):
        raise HTTPException(400, "状态只能是 active 或 pending")

    ent = Enterprise(
        name=name,
        industry=(req.industry or "").strip(),
        description=(req.description or "").strip(),
        contact_name=(req.contact_name or "").strip(),
        contact_email=(req.contact_email or "").strip(),
        status=status,
    )
    db.add(ent)
    await db.commit()
    await db.refresh(ent)

    return {
        "id": ent.id,
        "name": ent.name,
        "industry": ent.industry,
        "description": ent.description,
        "contact_name": ent.contact_name,
        "contact_email": ent.contact_email,
        "status": ent.status,
        "created_at": ent.created_at.isoformat() if ent.created_at else None,
    }


# 6. 修改企业合作状态
@router.put("/enterprises/{enterprise_id}/status")
async def update_enterprise_status(
    enterprise_id: str,
    req: EnterpriseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    ent = await db.get(Enterprise, enterprise_id)
    if not ent:
        raise HTTPException(404, "Enterprise not found")
    ent.status = req.status
    await db.commit()
    return ent


# 7. 获取所有企业发布的岗位列表（支持筛选 + 分页）
@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    # 构建过滤条件：未指定 status 时，默认排除已驳回的岗位（管理员不可见）
    conditions = []
    if status:
        conditions.append(JobPost.status == status)
    else:
        conditions.append(JobPost.status != "rejected")

    # 总数
    count_stmt = (
        select(func.count(JobPost.id))
        .join(Enterprise, JobPost.enterprise_id == Enterprise.id)
    )
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
    total = await db.scalar(count_stmt) or 0
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # 分页数据
    stmt = (
        select(JobPost, Enterprise.name.label("enterprise_name"))
        .join(Enterprise, JobPost.enterprise_id == Enterprise.id)
    )
    for cond in conditions:
        stmt = stmt.where(cond)
    stmt = stmt.order_by(desc(JobPost.created_at))

    offset = (page - 1) * page_size
    res = await db.execute(stmt.offset(offset).limit(page_size))

    jobs = []
    for row in res.all():
        jobs.append({
            "id": row[0].id,
            "enterprise_id": row[0].enterprise_id,
            "enterprise_name": row.enterprise_name,
            "title": row[0].title,
            "category": row[0].category,
            "description": row[0].description,
            "requirements_text": row[0].requirements_text,
            "status": row[0].status,
            "review_reason": row[0].review_reason,
            "created_at": row[0].created_at.isoformat() if row[0].created_at else None,
        })

    return {
        "items": jobs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# 8. 获取岗位详情及其能力特征指标
@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    job = await db.get(JobPost, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
        
    ent = await db.get(Enterprise, job.enterprise_id)
    ability_stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
    ability_res = await db.execute(ability_stmt)
    model = ability_res.scalar_one_or_none()
    
    return {
        "job": job,
        "enterprise": ent,
        "ability_model": model
    }


# 9. 审核通过企业岗位
@router.post("/jobs/{job_id}/approve")
async def approve_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    job = await db.get(JobPost, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
    job.status = "approved"
    job.review_reason = ""
    await db.commit()
    return job


# 10. 驳回企业岗位（必须提供非空的驳回原因）
@router.post("/jobs/{job_id}/reject")
async def reject_job(
    job_id: str,
    req: JobAuditRequest,
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    job = await db.get(JobPost, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
    # 校验：仅允许从待审核或已通过状态驳回
    if job.status not in ("pending_review", "approved"):
        raise HTTPException(400, f"当前状态「{job.status}」不允许驳回，仅待审核或已通过可驳回。")
    # 校验驳回原因不能为空
    reason = req.reason.strip()
    if not reason:
        raise HTTPException(400, "驳回原因不能为空，请填写具体的驳回理由。")
    job.status = "rejected"
    job.review_reason = reason
    await db.commit()
    return job


# 11. 获取学生 Agent 决策追踪（管理员专用）
@router.get("/students/{student_id}/traces")
async def get_student_traces(
    student_id: int,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _identity: Identity = Depends(require_admin),
):
    """管理员查看指定学生的 Agent 决策追踪记录。"""
    from core.services import agent_trace_service
    student = await db.get(Student, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    traces = await agent_trace_service.get_traces_by_student(db, student_id, limit=limit)
    return {"traces": traces, "total": len(traces)}
