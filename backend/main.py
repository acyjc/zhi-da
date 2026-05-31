# 职达 API 主入口——FastAPI 应用、CORS 中间件、路由注册、数据库初始化
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import CORS_ORIGINS
from db.database import init_db
from api.routes import student, job, diagnosis, progress, export, growth, resume, chat


# 应用启动时自动创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="职达 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(student.router)
app.include_router(job.router)
app.include_router(diagnosis.router)
app.include_router(progress.router)
app.include_router(export.router)
app.include_router(growth.router)
app.include_router(resume.router)
app.include_router(chat.router)


# 健康检查端点
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "TalentPath"}
