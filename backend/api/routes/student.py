# 学生管理路由——创建学生、查询学生、手动更新技能水平
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.models.student import StudentCreate, StudentUpdate, StudentResponse, SkillUpdateRequest
from core.services import student_service
from core.auth import get_current_identity, verify_student_access, Identity

router = APIRouter(prefix="/api/students", tags=["students"])


# 创建新学生（公开接口，注册时不需要 token）
@router.post("", response_model=StudentResponse)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    return await student_service.create_student(db, data)


# 根据 ID 获取学生（需要认证）
@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    return await student_service.get_student(db, student_id)


# 更新学生基本信息（需要认证）
@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    student = await student_service.update_student(db, student_id, data)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


# 手动更新学生技能水平（需要认证）
@router.put("/{student_id}/skills")
async def update_skills(
    student_id: int,
    data: SkillUpdateRequest,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    return await student_service.update_skills(db, student_id, data)
