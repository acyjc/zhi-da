# 全局配置——数据库连接、LLM 参数、文件上传限制、CORS 策略
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/db/talent_path.db")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE_MB = 10
ALLOWED_UPLOAD_TYPES = {".pdf", ".docx", ".txt", ".json"}
MAX_RESUME_LENGTH = 10000
MAX_EVIDENCE_LENGTH = 500
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
