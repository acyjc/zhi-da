# 时间工具——统一 UTC 时间获取，避免 datetime.utcnow() 的 DeprecationWarning
from datetime import datetime, UTC


def utc_now() -> datetime:
    """返回当前 UTC 时间（timezone-aware）。

    替代 datetime.utcnow()，消除 Python 3.12+ 的 DeprecationWarning。
    返回值为 timezone-aware datetime，SQLite/SQLAlchemy 兼容存储为 ISO 格式。
    """
    return datetime.now(UTC)
