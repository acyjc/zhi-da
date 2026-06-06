# 学校端管理后台路由——数据统计、学生列表、企业管理、岗位审核审核与驳回
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import Student, Enterprise, JobPost, JobAbilityModel, StudentAuthorization, DiagnosisResult

router = APIRouter(prefix="/api/admin", tags=["admin"])


class EnterpriseStatusUpdate(BaseModel):
    status: str  # active / disabled / pending


class JobAuditRequest(BaseModel):
    reason: Optional[str] = ""


# 1. 基础运营统计数据
@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
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


# 2. 获取学生列表
@router.get("/students")
async def list_students(db: AsyncSession = Depends(get_db)):
    stmt = select(Student).order_by(Student.created_at.desc())
    res = await db.execute(stmt)
    students = res.scalars().all()
    
    # 附带学生的诊断次数和最新的诊断分数
    output = []
    for s in students:
        diag_stmt = select(DiagnosisResult).where(DiagnosisResult.student_id == s.id).order_by(desc(DiagnosisResult.version))
        diag_res = await db.execute(diag_stmt)
        diags = diag_res.scalars().all()
        
        output.append({
            "id": s.id,
            "name": s.name,
            "grade": s.grade,
            "major": s.major,
            "target_job": s.target_job,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "diagnosis_count": len(diags),
            "latest_score": diags[0].match_score if diags else None,
        })
    return output


# 3. 获取特定学生诊断及授权详情
@router.get("/students/{student_id}")
async def get_student_detail(student_id: str, db: AsyncSession = Depends(get_db)):
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


# 4. 获取合作企业列表
@router.get("/enterprises")
async def list_enterprises(db: AsyncSession = Depends(get_db)):
    stmt = select(Enterprise).order_by(Enterprise.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


# 5. 获取企业详情
@router.get("/enterprises/{enterprise_id}")
async def get_enterprise(enterprise_id: str, db: AsyncSession = Depends(get_db)):
    ent = await db.get(Enterprise, enterprise_id)
    if not ent:
        raise HTTPException(404, "Enterprise not found")
    return ent


# 6. 修改企业合作状态
@router.put("/enterprises/{enterprise_id}/status")
async def update_enterprise_status(enterprise_id: str, req: EnterpriseStatusUpdate, db: AsyncSession = Depends(get_db)):
    ent = await db.get(Enterprise, enterprise_id)
    if not ent:
        raise HTTPException(404, "Enterprise not found")
    ent.status = req.status
    await db.commit()
    return ent


# 7. 获取所有企业发布的岗位列表 (支持筛选待审核等状态)
@router.get("/jobs")
async def list_jobs(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(JobPost, Enterprise.name.label("enterprise_name")).join(Enterprise, JobPost.enterprise_id == Enterprise.id)
    if status:
        stmt = stmt.where(JobPost.status == status)
    stmt = stmt.order_by(desc(JobPost.created_at))
    res = await db.execute(stmt)
    
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
    return jobs


# 8. 获取岗位详情及其能力特征指标
@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
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
async def approve_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(JobPost, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
    job.status = "approved"
    job.review_reason = ""
    await db.commit()
    return job


# 10. 驳回企业岗位
@router.post("/jobs/{job_id}/reject")
async def reject_job(job_id: str, req: JobAuditRequest, db: AsyncSession = Depends(get_db)):
    job = await db.get(JobPost, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
    job.status = "rejected"
    job.review_reason = req.reason or "能力模型或JD填写不符合规范"
    await db.commit()
    return job
