# 岗位管理路由——岗位列表、岗位详情
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.models.job import JobResponse
from core.services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# 获取全部岗位列表
@router.get("", response_model=list[JobResponse])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    return await job_service.list_jobs(db)


# 获取单个岗位详情
@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    return await job_service.get_job(db, job_id)
