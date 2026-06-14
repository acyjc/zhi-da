# 岗位管理服务——创建、列表查询、详情查询
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import Job as JobORM
from core.models.job import JobCreate, JobResponse


async def create_job(db: AsyncSession, data: JobCreate) -> JobResponse:
    job = JobORM(**data.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return JobResponse.model_validate(job)


async def list_jobs(db: AsyncSession) -> list[JobResponse]:
    result = await db.execute(select(JobORM))
    jobs = result.scalars().all()
    return [JobResponse.model_validate(j) for j in jobs]


async def get_job(db: AsyncSession, job_id: str) -> JobResponse | None:
    result = await db.execute(select(JobORM).where(JobORM.id == job_id))
    job = result.scalar_one_or_none()
    return JobResponse.model_validate(job) if job else None
