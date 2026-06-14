# 全局配置——数据库连接、LLM 参数、文件上传限制、CORS 策略
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DATA_DIR}/talent_path.db")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_UPLOAD_TYPES = {".pdf", ".docx", ".txt", ".json"}
ALLOWED_ATTACHMENT_TYPES = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".docx"}
MAX_RESUME_LENGTH = 10000
MAX_EVIDENCE_LENGTH = 500
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# 轻量身份会话（JWT）
JWT_SECRET = os.getenv("JWT_SECRET", "zhida-dev-secret-key-change-in-production-2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h
ADMIN_ACCOUNT = os.getenv("ADMIN_ACCOUNT", "admin")
