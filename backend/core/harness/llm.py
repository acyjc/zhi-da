# LLM 抽象层——统一 LLMClient 接口，支持 OpenAI 实现和 Mock 规则提取实现
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator
import re
import json
from config.settings import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


@dataclass
class LLMResponse:
    content: str = ""
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)


@dataclass
class LLMChunk:
    content: str = ""
    finish_reason: str = ""


# LLM 客户端抽象基类
class LLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        ...


# OpenAI 异步客户端实现
class OpenAIClient(LLMClient):
    def __init__(self):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        kwargs = {"model": LLM_MODEL, "messages": messages, "temperature": 0.3}
        if tools:
            kwargs["tools"] = tools
        response = await self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            finish_reason=choice.finish_reason or "stop",
            usage={"prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                   "completion_tokens": response.usage.completion_tokens if response.usage else 0},
        )

    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        kwargs = {"model": LLM_MODEL, "messages": messages, "temperature": 0.3, "stream": True}
        if tools:
            kwargs["tools"] = tools
        stream = await self._client.chat.completions.create(**kwargs)
        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield LLMChunk(content=delta.content, finish_reason=chunk.choices[0].finish_reason or "")
            elif chunk.choices and chunk.choices[0].finish_reason:
                yield LLMChunk(content="", finish_reason=chunk.choices[0].finish_reason)


# 技能关键词库——用于 Mock 模式从简历文本中提取技能
TECH_SKILLS_DICT = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
    "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
    "Spring Boot", "MySQL", "PostgreSQL", "MongoDB", "Redis", "SQL",
    "Docker", "Kubernetes", "Linux", "Git", "AWS", "Nginx",
    "HTML", "CSS", "RESTful", "GraphQL", "Webpack", "Vite",
    "机器学习", "深度学习", "数据挖掘", "NLP", "计算机视觉",
    "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy",
    "Hadoop", "Spark", "Kafka", "RabbitMQ", "Elasticsearch",
]
SOFT_SKILLS_DICT = [
    "沟通表达", "团队协作", "学习能力", "逻辑思维", "项目管理",
    "领导力", "时间管理", "抗压能力", "创新思维", "文档编写",
]
DOMAIN_DICT = [
    "Web开发", "移动开发", "后端开发", "前端开发", "数据分析",
    "人工智能", "云计算", "微服务", "数据库", "操作系统",
    "网络编程", "测试", "DevOps", "安全", "嵌入式",
]


def _extract_user_text(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""


def _mock_parse_resume(text: str) -> dict:
    text_lower = text.lower()
    result: dict = {}

    name_match = re.search(r'[姓名][：:\s]*([^\s,，。\n]{2,4})', text)
    if name_match:
        result["name"] = name_match.group(1)
    else:
        first_line = text.strip().split('\n')[0].strip()
        first_word = first_line.split()[0] if first_line.split() else ''
        if 2 <= len(first_word) <= 4 and re.match(r'^[\u4e00-\u9fff]+$', first_word):
            result["name"] = first_word

    grade_match = re.search(r'(大一|大二|大三|大四|研一|研二|研三|201\d|202\d)', text)
    if grade_match:
        result["grade"] = grade_match.group(1)
    else:
        result["grade"] = ""

    major_match = re.search(r'(计算机科学|软件工程|数据科学|人工智能|电子信息|通信工程|自动化|信息管理|数学|统计)', text)
    if major_match:
        result["major"] = major_match.group(1)
    else:
        result["major"] = ""

    tech_skills: dict = {}
    for skill in TECH_SKILLS_DICT:
        if skill.lower() in text_lower:
            skill_pattern = re.compile(rf'{re.escape(skill)}', re.IGNORECASE)
            mentions = len(skill_pattern.findall(text))
            if mentions >= 3:
                tech_skills[skill] = 80
            elif mentions >= 2:
                tech_skills[skill] = 65
            else:
                tech_skills[skill] = 50
    result["tech_skills"] = tech_skills

    soft_skills: dict = {}
    for skill in SOFT_SKILLS_DICT:
        if skill in text:
            soft_skills[skill] = 65
    if not soft_skills:
        soft_skills = {"沟通表达": 60, "团队协作": 60, "学习能力": 60}
    result["soft_skills"] = soft_skills

    domain_knowledge: dict = {}
    for domain in DOMAIN_DICT:
        if domain in text:
            domain_knowledge[domain] = 60
    result["domain_knowledge"] = domain_knowledge

    projects = []
    proj_matches = re.findall(
        r'(?:项目|课题).*?[：:\s]*([^\n]{5,60})',
        text
    )
    for i, pm in enumerate(proj_matches[:3]):
        projects.append({
            "name": pm.strip(),
            "role": "开发工程师",
            "description": pm.strip(),
            "duration": "",
        })
    result["project_exp"] = projects

    target = ""
    if tech_skills:
        top = sorted(tech_skills.items(), key=lambda x: x[1], reverse=True)[:3]
        top_names = [t[0] for t in top]
        if any(s in top_names for s in ["Python", "Java", "Go", "Django", "Spring"]):
            target = "后端开发工程师"
        elif any(s in top_names for s in ["React", "Vue", "Angular", "HTML", "CSS"]):
            target = "前端开发工程师"
        elif any(s in top_names for s in ["机器学习", "深度学习", "PyTorch", "TensorFlow"]):
            target = "AI算法工程师"
        elif any(s in top_names for s in ["Pandas", "NumPy", "数据分析"]):
            target = "数据分析师"
        else:
            target = "Python后端开发工程师"
    result["target_job"] = target

    result["summary"] = f"基于规则匹配解析：识别到{len(tech_skills)}项技术技能、{len(projects)}个项目经历（Mock 模式）"
    return result


# 无 API Key 时的 Mock 实现——用规则从输入文本中提取信息
class MockLLMClient(LLMClient):
    async def complete(self, messages: list[dict], tools: list[dict] = None) -> LLMResponse:
        text = _extract_user_text(messages)
        system = messages[0].get("content", "") if messages else ""
        if "简历解析" in system or "简历文本" in system or "解析以下简历" in text:
            result = _mock_parse_resume(text)
        else:
            result = {"message": "Mock模式：未配置LLM，请设置LLM_API_KEY环境变量后在.env中填入"}
        return LLMResponse(
            content=json.dumps(result, ensure_ascii=False),
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    async def stream(self, messages: list[dict], tools: list[dict] = None) -> AsyncIterator[LLMChunk]:
        yield LLMChunk(content='{"result": "mock_stream"}', finish_reason="stop")


# 获取 LLM 客户端实例，优先 OpenAI，无 Key 则降级为 Mock
def get_llm_client() -> LLMClient:
    if LLM_API_KEY:
        try:
            return OpenAIClient()
        except ImportError:
            pass
    return MockLLMClient()
