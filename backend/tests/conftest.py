import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Union

from core.auth import create_token


def auth_headers(role: str, *, student_id: Union[int, str] = 0, enterprise_id: str = "",
                 admin_account: str = "") -> dict:
    """生成用于 TestClient 的认证请求头。"""
    token_data = create_token(
        role,
        student_id=student_id,
        enterprise_id=enterprise_id,
        admin_account=admin_account,
    )
    return {"Authorization": f"Bearer {token_data['access_token']}"}
