# 职达 API 主入口——FastAPI 应用、CORS 中间件、路由注册、数据库初始化
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import CORS_ORIGINS, LLM_API_KEY
from db.database import init_db
from api.routes import student, job, diagnosis, export, resume, student_ext, enterprise, admin
from api.routes import agent, growth_tasks, auth, attachment, agent_trace, conversation


# 应用启动时自动创建数据库表
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="职达 API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# 认证路由（登录/登出）
app.include_router(auth.router)
# 核心业务路由
app.include_router(student.router)
app.include_router(job.router)
app.include_router(diagnosis.router)
app.include_router(export.router)
app.include_router(resume.router)
# 三端协同路由
app.include_router(student_ext.router)
app.include_router(enterprise.router)
app.include_router(admin.router)
# 智能体与成长任务路由
app.include_router(agent.router)
app.include_router(growth_tasks.router)
# Agent 决策追踪路由
app.include_router(agent_trace.router)
# 对话历史路由
app.include_router(conversation.router)
# 附件管理路由
app.include_router(attachment.router)


# 健康检查端点（含 AI 状态）
@app.get("/api/health")
async def health():
    ai_configured = bool(LLM_API_KEY.strip())
    return {
        "status": "ok",
        "service": "TalentPath",
        "version": "2.0.0",
        "ai_status": "configured" if ai_configured else "missing_key",
        "ai_available": ai_configured,
    }
