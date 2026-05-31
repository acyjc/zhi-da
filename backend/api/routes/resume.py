# 简历解析路由——文本解析 + 文件上传解析，调用 LLM 提取结构化信息
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from db.database import get_db
from core.harness.llm import get_llm_client
from config.settings import MAX_UPLOAD_SIZE_MB, ALLOWED_UPLOAD_TYPES
import json
import re
import os

router = APIRouter(prefix="/api/resume", tags=["resume"])

SYSTEM_PROMPT = """你是一个专业的简历解析助手。从简历文本中提取以下信息，以严格JSON格式返回：

{
  "name": "姓名",
  "grade": "年级(如大三/研二，无法判断为空)",
  "major": "专业",
  "target_job": "目标岗位(推断最匹配的岗位方向)",
  "tech_skills": {"技能名": 分值(0-100)},
  "soft_skills": {"技能名": 分值(0-100)},
  "domain_knowledge": {"领域名": 分值(0-100)},
  "project_exp": [{"name": "项目名", "role": "角色", "description": "简述", "duration": "时长"}],
  "summary": "一句话能力总结"
}

规则：
1. 分值基于简历描述的熟练程度推断：精通90+、熟练75-85、了解60-70、接触40-55
2. 软技能从项目角色、团队协作描述中推断
3. 领域知识从技术栈、项目方向中推断
4. 所有字段都必须存在，可以为空字符串/空数组/空对象
5. 只返回JSON，不要任何额外文字"""


class ResumeParseRequest(BaseModel):
    resume_text: str


class ResumeParseResponse(BaseModel):
    name: str = ""
    grade: str = ""
    major: str = ""
    target_job: str = ""
    tech_skills: dict = {}
    soft_skills: dict = {}
    domain_knowledge: dict = {}
    project_exp: list = []
    summary: str = ""


# 从上传文件中提取纯文本，支持 PDF/DOCX/TXT
async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        from PyPDF2 import PdfReader
        import io
        reader = PdfReader(io.BytesIO(content))
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)
    elif ext == ".docx":
        from docx import Document
        import io
        doc = Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    else:
        return content.decode("utf-8", errors="ignore")


# 调用 LLM 解析简历文本，返回结构化数据
async def parse_resume_with_llm(text: str) -> ResumeParseResponse:
    llm = get_llm_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"请解析以下简历：\n\n{text[:6000]}"},
    ]
    response = await llm.complete(messages)
    try:
        data = json.loads(response.content)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', response.content)
        data = json.loads(match.group(0)) if match else {}

    return ResumeParseResponse(
        name=data.get("name", ""),
        grade=data.get("grade", ""),
        major=data.get("major", ""),
        target_job=data.get("target_job", ""),
        tech_skills=data.get("tech_skills", {}) or {},
        soft_skills=data.get("soft_skills", {}) or {},
        domain_knowledge=data.get("domain_knowledge", {}) or {},
        project_exp=data.get("project_exp", []) or [],
        summary=data.get("summary", ""),
    )


# 提交简历文本，返回解析后的结构化数据
@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(req: ResumeParseRequest, db: AsyncSession = Depends(get_db)):
    return await parse_resume_with_llm(req.resume_text)


# 上传简历文件(PDF/DOCX/TXT)，提取文本后调用 LLM 解析
@router.post("/upload", response_model=ResumeParseResponse)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_TYPES:
        return ResumeParseResponse()
    if file.size and file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        return ResumeParseResponse()

    text = await extract_text_from_file(file)
    if not text.strip():
        return ResumeParseResponse()

    return await parse_resume_with_llm(text)
