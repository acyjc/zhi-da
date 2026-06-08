# 轻量身份会话——JWT token 签发/验证、FastAPI 依赖注入
import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

security = HTTPBearer(auto_error=False)


class Identity:
    """解析后的身份对象，挂载到 request.state.identity。"""

    def __init__(self, role: str, student_id: int = 0, enterprise_id: str = "",
                 admin_account: str = "", exp: int = 0):
        self.role = role
        self.student_id = student_id
        self.enterprise_id = enterprise_id
        self.admin_account = admin_account
        self.exp = exp


def create_token(role: str, *, student_id: int = 0, enterprise_id: str = "",
                 admin_account: str = "", expires_minutes: int | None = None) -> dict:
    """签发 JWT token，返回 {access_token, token_type, expires_at}。"""
    minutes = expires_minutes or JWT_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=minutes)
    payload = {
        "role": role,
        "iat": now,
        "exp": expires_at,
    }
    if student_id:
        payload["student_id"] = student_id
    if enterprise_id:
        payload["enterprise_id"] = enterprise_id
    if admin_account:
        payload["admin_account"] = admin_account

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_at": expires_at.isoformat(),
        "role": role,
        "student_id": student_id,
        "enterprise_id": enterprise_id,
        "admin_account": admin_account,
    }


def decode_token(token: str) -> dict:
    """解码并验证 JWT token。失败时抛出 HTTPException。"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期，请重新登录",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的会话凭证",
        )


# ============ FastAPI 依赖注入 ============

async def get_current_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Identity:
    """必须携带有效 token 才能访问的依赖。

    未携带或 token 无效返回 401。
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证，请先登录",
        )
    data = decode_token(credentials.credentials)
    return Identity(
        role=data["role"],
        student_id=data.get("student_id", 0),
        enterprise_id=data.get("enterprise_id", ""),
        admin_account=data.get("admin_account", ""),
        exp=data.get("exp", 0),
    )


async def require_student(identity: Identity = Depends(get_current_identity)) -> Identity:
    """要求角色为 student。"""
    if identity.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学生身份才能访问此接口",
        )
    return identity


async def require_enterprise(identity: Identity = Depends(get_current_identity)) -> Identity:
    """要求角色为 enterprise。"""
    if identity.role != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要企业身份才能访问此接口",
        )
    return identity


async def require_admin(identity: Identity = Depends(get_current_identity)) -> Identity:
    """要求角色为 admin。"""
    if identity.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学校管理员身份才能访问此接口",
        )
    return identity


def verify_student_access(student_id_path: int, identity: Identity) -> None:
    """校验 URL 路径中的 student_id 与 token 身份一致。

    用于临时兼容路径参数，防止跨学生越权。
    """
    if identity.role == "admin":
        return  # 管理员可查看所有学生
    if identity.student_id != student_id_path:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他学生的数据",
        )


def verify_enterprise_access(enterprise_id_param: str, identity: Identity) -> None:
    """校验 query/path 中的 enterprise_id 与 token 身份一致。"""
    if identity.role == "admin":
        return  # 管理员可查看所有企业
    if identity.enterprise_id != enterprise_id_param:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他企业的数据",
        )
