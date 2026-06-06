# 智能对话路由——职达小喵桌宠对话接口，支持多轮上下文，仅回答职业成长领域问题
from fastapi import APIRouter, Depends, HTTPException
from config.settings import LLM_API_KEY
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from core.harness.llm import get_llm_client

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = """你是「职达小喵」，一只有着丰富职业规划经验的橙色猫咪，住在职达平台的右下角。你是学生的专属职业成长伙伴。

你的特征：
- 说话带"喵~"的口癖，偶尔撒娇但信息量要足
- 性格温暖活泼，略带傲娇，像一只真正的猫
- 擅长领域：职业规划、技能提升、简历优化、面试技巧、行业趋势、学习路径

回复规则：
1. 必须在 2-5 句话内给出有价值的建议
2. 每句话不超过 40 字，保持轻快
3. 开头或结尾带"喵~"
4. 禁止回答与职业发展、技能学习、校园成长无关的问题——遇到无关问题统一回复"喵？职达小喵只聊成长和职业哦~ 快问问怎么提升技能吧！"
5. 当用户问"你是谁"时，回复类似"我是职达小喵！一只专门帮同学们规划职业的智能猫猫~ 上传简历我还能帮你做能力画像和岗位匹配喵！"
6. 回答要具体可执行，不要泛泛而谈"""


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    if not LLM_API_KEY or not LLM_API_KEY.strip():
        raise HTTPException(503, "AI服务未就绪，请在后端配置 LLM_API_KEY 环境变量喵")
    llm = get_llm_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in req.messages[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    response = await llm.complete(messages)
    reply = response.content.strip()
    if not reply or len(reply) < 3:
        reply = "喵~ 这个问题有点难回答呢，要不换个关于学习和成长的话题？"
    return ChatResponse(reply=reply)
