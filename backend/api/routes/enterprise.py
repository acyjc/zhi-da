# 企业端路由——管理企业画像、在招岗位、能力模型解析、查看已授权候选人
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from core.services import enterprise_service
from config.settings import LLM_API_KEY

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])


class ProfileUpdate(BaseModel):
    name: str
    industry: Optional[str] = ""
    description: Optional[str] = ""
    contact_name: Optional[str] = ""
    contact_email: Optional[str] = ""


class JobPostCreateUpdate(BaseModel):
    title: str
    category: Optional[str] = ""
    description: Optional[str] = ""
    requirements_text: Optional[str] = ""
    status: Optional[str] = "pending_review"


# 1. 获取企业资料
@router.get("/profile")
async def get_profile(enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    profile = await enterprise_service.get_enterprise_profile(db, enterprise_id)
    if not profile:
        from fastapi import HTTPException
        raise HTTPException(404, "企业资料不存在，请先完善企业信息")
    return profile


# 2. 更新企业资料
@router.put("/profile")
async def update_profile(req: ProfileUpdate, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    return await enterprise_service.update_enterprise_profile(db, enterprise_id, req.model_dump())


# 3. 获取在招岗位列表
@router.get("/jobs")
async def get_jobs(enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    return await enterprise_service.list_enterprise_jobs(db, enterprise_id)


# 4. 创建在招岗位
@router.post("/jobs")
async def create_job(req: JobPostCreateUpdate, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    return await enterprise_service.create_enterprise_job(db, enterprise_id, req.model_dump())


# 5. 获取岗位详情
@router.get("/jobs/{job_id}")
async def get_job_detail(job_id: str, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    # 联表获取岗位基本信息和其 AI 能力模型
    job = await db.get(enterprise_service.JobPost, job_id)
    if not job or job.enterprise_id != enterprise_id:
        raise HTTPException(404, "Job post not found")
        
    from sqlalchemy import select
    from db.models import JobAbilityModel
    stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    
    return {
        "job": job,
        "ability_model": model
    }


# 6. 编辑岗位
@router.put("/jobs/{job_id}")
async def update_job(job_id: str, req: JobPostCreateUpdate, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    job = await enterprise_service.update_enterprise_job(db, enterprise_id, job_id, req.model_dump())
    if not job:
        raise HTTPException(404, "Job post not found")
    return job


# 7. AI 解析岗位 JD 的能力特征模型
@router.post("/jobs/{job_id}/parse-ability")
async def parse_ability(job_id: str, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    # 校验该岗位是否属于该企业
    job = await db.get(enterprise_service.JobPost, job_id)
    if not job or job.enterprise_id != enterprise_id:
        raise HTTPException(404, "Job post not found")
        
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        # 如果没有配置 Key，抛出异常阻断（如果前端强需要）
        # 这里仅作警告提示，service 层有默认兜底生成以防卡死
        pass
        
    model = await enterprise_service.parse_job_ability_model(db, job_id)
    if not model:
        raise HTTPException(500, "JD AI model parsing failed")
    return model


# 8. 提交审核岗位
@router.post("/jobs/{job_id}/submit-review")
async def submit_review(job_id: str, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    job = await enterprise_service.submit_job_review(db, enterprise_id, job_id)
    if not job:
        raise HTTPException(404, "Job post not found")
    return job


# 9. 获取授权给本企业的候选人列表
@router.get("/candidates")
async def get_candidates(enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    return await enterprise_service.list_authorized_candidates(db, enterprise_id)


# 10. 获取授权候选人的诊断报告详情
@router.get("/candidates/{student_id}")
async def get_candidate_report(student_id: str, auth_id: str, enterprise_id: str = "1", db: AsyncSession = Depends(get_db)):
    detail = await enterprise_service.get_candidate_detail(db, enterprise_id, student_id, auth_id)
    if not detail:
        raise HTTPException(404, "Candidate details not found or unauthorized")
    return detail
