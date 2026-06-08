# 企业端路由——管理企业画像、在招岗位、能力模型解析、查看已授权候选人
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import Enterprise
from core.services import enterprise_service
from core.auth import require_enterprise, Identity
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
    status: Optional[str] = "draft"


async def _check_enterprise_active(db: AsyncSession, enterprise_id: str) -> Enterprise:
    """企业状态门禁：只有 active 状态的企业才能进入业务流。"""
    ent = await db.get(Enterprise, enterprise_id)
    if not ent:
        raise HTTPException(404, "企业不存在，请先注册企业信息")
    if ent.status == "pending":
        raise HTTPException(403, f"企业「{ent.name}」尚未通过审核（状态：pending），暂不可操作。请联系学校管理员审核。")
    if ent.status == "disabled":
        raise HTTPException(403, f"企业「{ent.name}」已被禁用（状态：disabled），不可操作。请联系学校管理员。")
    return ent


def _eid(identity: Identity, enterprise_id: str | None = None) -> str:
    """从 token 推导 enterprise_id，忽略 query 参数。"""
    return identity.enterprise_id


# 1. 获取企业资料
@router.get("/profile")
async def get_profile(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    profile = await enterprise_service.get_enterprise_profile(db, eid)
    if not profile:
        raise HTTPException(404, "企业资料不存在，请先完善企业信息")
    return profile


# 2. 更新企业资料
@router.put("/profile")
async def update_profile(
    req: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    ent = await db.get(Enterprise, eid)
    if ent and ent.status == "disabled":
        raise HTTPException(403, f"企业「{ent.name}」已被禁用，不可修改资料。")
    return await enterprise_service.update_enterprise_profile(db, eid, req.model_dump())


# 3. 获取在招岗位列表
@router.get("/jobs")
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    return await enterprise_service.list_enterprise_jobs(db, eid)


# 4. 创建在招岗位
@router.post("/jobs")
async def create_job(
    req: JobPostCreateUpdate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    return await enterprise_service.create_enterprise_job(db, eid, req.model_dump())


# 5. 获取岗位详情
@router.get("/jobs/{job_id}")
async def get_job_detail(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    job = await db.get(enterprise_service.JobPost, job_id)
    if not job or job.enterprise_id != eid:
        raise HTTPException(404, "Job post not found")

    from db.models import JobAbilityModel
    stmt = select(JobAbilityModel).where(JobAbilityModel.job_post_id == job_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()

    return {"job": job, "ability_model": model}


# 6. 编辑岗位
@router.put("/jobs/{job_id}")
async def update_job(
    job_id: str,
    req: JobPostCreateUpdate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    job = await enterprise_service.update_enterprise_job(db, eid, job_id, req.model_dump())
    if not job:
        raise HTTPException(404, "Job post not found")
    return job


# 7. AI 解析岗位 JD 的能力特征模型
@router.post("/jobs/{job_id}/parse-ability")
async def parse_ability(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    job = await db.get(enterprise_service.JobPost, job_id)
    if not job or job.enterprise_id != eid:
        raise HTTPException(404, "Job post not found")

    model = await enterprise_service.parse_job_ability_model(db, job_id)
    if not model:
        raise HTTPException(500, "JD AI model parsing failed")
    return model


# 8. 提交审核岗位
@router.post("/jobs/{job_id}/submit-review")
async def submit_review(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    try:
        job = await enterprise_service.submit_job_review(db, eid, job_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not job:
        raise HTTPException(404, "Job post not found")
    return job


# 9. 获取授权给本企业的候选人列表
@router.get("/candidates")
async def get_candidates(
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    return await enterprise_service.list_authorized_candidates(db, eid)


# 10. 获取授权候选人的诊断报告详情
@router.get("/candidates/{student_id}")
async def get_candidate_report(
    student_id: int,
    auth_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_enterprise),
):
    eid = _eid(identity)
    await _check_enterprise_active(db, eid)
    detail = await enterprise_service.get_candidate_detail(db, eid, student_id, auth_id)
    if not detail:
        raise HTTPException(404, "Candidate details not found or unauthorized")
    return detail
