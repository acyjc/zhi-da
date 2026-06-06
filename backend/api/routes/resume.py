# 简历解析路由——文本解析 + 文件上传解析，调用 LLM 提取结构化信息
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from db.database import get_db
from core.harness.llm import get_llm_client
from config.settings import MAX_UPLOAD_SIZE_MB, ALLOWED_UPLOAD_TYPES
import json
import re
import os
import logging

router = APIRouter(prefix="/api/resume", tags=["resume"])
logger = logging.getLogger("zhi-da.resume")

RESUME_OUTPUT_SCHEMA = """{
  "name": "<姓名，2-4字中文或英文全名>",
  "grade": "<大一|大二|大三|大四|研一|研二|研三|空字符串>",
  "major": "<专业名称>",
  "target_job": "<推断的岗位方向，如：后端开发工程师 / 前端开发工程师 / AI算法工程师 / 数据分析师>",
  "tech_skills": { "<技能名>": <0-100分值> },
  "soft_skills": { "<软技能名>": <0-100分值> },
  "domain_knowledge": { "<领域名>": <0-100分值> },
  "project_exp": [
    {
      "name": "<项目名称>",
      "role": "<担任角色，如：后端开发 / 前端开发 / 项目负责人>",
      "description": "<1-2句话描述>",
      "duration": "<时间段，如：2023.09-2024.01>"
    }
  ],
  "summary": "<一句话能力总结>"
}"""

SYSTEM_PROMPT = f"""你是一个专业的简历解析助手。请严格按照以下JSON Schema解析简历：

{ RESUME_OUTPUT_SCHEMA }

## 解析规则

### 姓名
- 优先从"姓名："、"名字："标签提取
- 否则取首行开头2-4个中文字，或首行英文名如"Tom Zhang"
- 如完全无法判断，返回空字符串

### 年级
- 匹配"大一/大二/大三/大四/研一/研二/研三"或入学年份（2019→推算大四）
- 无法判断返回空字符串

### 专业
- 匹配专业关键词："计算机科学/软件工程/数据科学/人工智能/电子信息/通信工程/自动化/数学/统计"等
- 无法判断提取简历中最可能的专业名

### 技术技能评分
- **精通**（简历写"精通/深入理解/源码级/架构设计"）→ 90-100
- **熟练**（简历写"熟练/独立开发/负责过"）→ 75-85
- **掌握**（简历写"掌握/熟悉/使用过"）→ 60-70
- **了解**（简历只提了名字/课程学过）→ 40-55
- 每个技能评分必须有依据，不要所有技能同一分值

### 软技能
- 从项目描述中推断：参与团队项目的→"团队协作"、做过汇报答辩的→"沟通表达"、负责多任务的→"项目管理"
- 至少返回1-3个，不要返回空对象

### 领域知识
- 根据简历中的技术栈推断："Spring/MyBatis"→"后端开发"、"Vue/React"→"前端开发"、"PyTorch/TensorFlow"→"深度学习"

### 项目经历
- 从"项目经验/实习经历/项目实践"等段落提取
- 每个项目必须包含name、role、description三个字段
- 如简历中无明确项目段落，`project_exp` 返回空数组 `[]`

### 目标岗位
- 根据技能聚类推断最匹配的岗位方向

## 强制要求
1. **只返回上述JSON Schema格式的纯JSON**，不要任何解释文字
2. 不要包裹在 ```json ``` 代码块中
3. 所有字段都必须存在，可为空字符串/空对象/空数组
4. tech_skills分值必须有区分度，不要全是相同分值"""


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


def _extract_json(text: str) -> dict:
    text = text.strip()
    code_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
    if code_match:
        text = code_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从LLM返回中提取JSON，原始返回前200字：{text[:200]}")


def _validate_and_clean(data: dict) -> dict:
    result: dict = {}

    for field in ["name", "grade", "major", "target_job", "summary"]:
        val = data.get(field, "")
        result[field] = str(val).strip() if isinstance(val, str) else ""

    for field in ["tech_skills", "soft_skills", "domain_knowledge"]:
        val = data.get(field, {})
        if not isinstance(val, dict):
            val = {}
        cleaned = {}
        for k, v in val.items():
            if isinstance(v, (int, float)):
                cleaned[str(k)] = max(0, min(100, int(v)))
            elif isinstance(v, str) and v.isdigit():
                cleaned[str(k)] = max(0, min(100, int(v)))
        result[field] = cleaned

    projects = data.get("project_exp", [])
    if not isinstance(projects, list):
        projects = []
    cleaned_projects = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        cleaned_projects.append({
            "name": name,
            "role": str(p.get("role", "")).strip() or "开发工程师",
            "description": str(p.get("description", "")).strip() or name,
            "duration": str(p.get("duration", "")).strip(),
        })
    result["project_exp"] = cleaned_projects

    return result


async def parse_resume_with_llm(text: str) -> ResumeParseResponse:
    from config.settings import LLM_API_KEY
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise HTTPException(503, "AI服务未就绪，请在后端配置 LLM_API_KEY 环境变量")
    llm = get_llm_client()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"请解析以下简历：\n\n{text[:6000]}"},
    ]
    logger.info("开始LLM简历解析，文本长度=%d", len(text))
    response = await llm.complete(messages)
    logger.info("LLM原始返回(前200字): %s", response.content[:200])

    data = _extract_json(response.content)
    logger.info("JSON提取成功，字段: %s", list(data.keys()))

    cleaned = _validate_and_clean(data)
    logger.info("校验完成: name=%s skills=%d projects=%d job=%s",
                cleaned["name"], len(cleaned["tech_skills"]),
                len(cleaned["project_exp"]), cleaned["target_job"])

    return ResumeParseResponse(
        name=cleaned["name"],
        grade=cleaned["grade"],
        major=cleaned["major"],
        target_job=cleaned["target_job"],
        tech_skills=cleaned["tech_skills"],
        soft_skills=cleaned["soft_skills"],
        domain_knowledge=cleaned["domain_knowledge"],
        project_exp=cleaned["project_exp"],
        summary=cleaned["summary"],
    )


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text
        import io
        return extract_text(io.BytesIO(content))
    except ImportError:
        pass
    try:
        from PyPDF2 import PdfReader
        import io
        reader = PdfReader(io.BytesIO(content))
        texts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
        return "\n".join(texts)
    except Exception:
        return ""


def _extract_docx_text(content: bytes) -> str:
    try:
        from docx import Document
        import io
        doc = Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception:
        return ""


async def extract_text_from_file(file: UploadFile) -> str:
    content = await file.read()
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        text = _extract_pdf_text(content)
        logger.info("PDF提取: %d 字符", len(text))
        if not text.strip():
            logger.warning("PDF文本为空，可能为扫描版PDF")
        return text
    elif ext == ".docx":
        return _extract_docx_text(content)
    else:
        return content.decode("utf-8", errors="ignore")


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(req: ResumeParseRequest, db: AsyncSession = Depends(get_db)):
    return await parse_resume_with_llm(req.resume_text)


@router.post("/upload", response_model=ResumeParseResponse)
async def upload_resume(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, f"不支持的文件类型：{ext}，请上传 PDF/DOCX/TXT")
    if file.size and file.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"文件过大（>{MAX_UPLOAD_SIZE_MB}MB）")

    text = await extract_text_from_file(file)
    if not text.strip():
        raise HTTPException(400, "未能从文件中提取到文字，可能为扫描版PDF，请粘贴文本内容")

    return await parse_resume_with_llm(text)
