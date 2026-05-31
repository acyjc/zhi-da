# 成长记录路由——查询学生的成长变化历史
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import GrowthRecord

router = APIRouter(prefix="/api/growth", tags=["growth"])


@router.get("/records/{student_id}")
async def get_growth_records(student_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GrowthRecord).where(GrowthRecord.student_id == student_id).order_by(GrowthRecord.created_at.desc()))
    records = result.scalars().all()
    return [{
        "id": r.id, "student_id": r.student_id, "record_type": r.record_type,
        "description": r.description, "before_snapshot": r.before_snapshot,
        "after_snapshot": r.after_snapshot,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in records]
