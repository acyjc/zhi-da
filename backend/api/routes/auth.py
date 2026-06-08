# 认证路由——轻量身份会话登录/登出
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import Student, Enterprise
from core.auth import create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    role: str
    identifier: str
    password: Optional[str] = ""


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """轻量登录入口。

    当前阶段不校验密码（表单保留密码框），仅验证身份标识存在。
    签发 JWT token 供后续 API 鉴权使用。
    """
    if req.role == "student":
        try:
            sid = int(req.identifier)
        except (ValueError, TypeError):
            raise HTTPException(400, "学生 ID 必须为纯数字")
        student = await db.get(Student, sid)
        if not student:
            raise HTTPException(404, "学生不存在，请先创建档案")
        token_data = create_token("student", student_id=student.id)
        return {**token_data, "student_id": student.id}

    if req.role == "enterprise":
        ent = await db.get(Enterprise, req.identifier)
        if not ent:
            raise HTTPException(404, "企业不存在")
        if ent.status != "active":
            reason = (
                "该企业尚未通过审核" if ent.status == "pending"
                else "该企业已被禁用" if ent.status == "disabled"
                else "该企业状态异常"
            )
            raise HTTPException(403, reason)
        token_data = create_token("enterprise", enterprise_id=ent.id)
        return {**token_data, "enterprise_id": ent.id}

    if req.role == "admin":
        from config.settings import ADMIN_ACCOUNT
        if req.identifier and req.identifier != ADMIN_ACCOUNT:
            raise HTTPException(403, "学校管理员账号不正确")
        token_data = create_token("admin", admin_account=req.identifier or ADMIN_ACCOUNT)
        return token_data

    raise HTTPException(400, "未知角色类型")


@router.post("/logout")
async def logout():
    """登出（前端清理 token，后端仅返回成功）。"""
    return {"status": "ok", "message": "已登出"}


@router.get("/enterprises")
async def list_enterprises_for_login(db: AsyncSession = Depends(get_db)):
    """公开接口：返回企业列表供登录页面下拉选择。"""
    from sqlalchemy import select
    from db.models import Enterprise
    stmt = select(Enterprise).order_by(Enterprise.created_at.desc())
    result = await db.execute(stmt)
    enterprises = result.scalars().all()
    return [
        {
            "id": e.id,
            "name": e.name,
            "status": e.status,
            "industry": e.industry if hasattr(e, "industry") else "",
        }
        for e in enterprises
    ]
