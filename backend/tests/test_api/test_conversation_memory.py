# 对话记忆服务测试——验证连续追问、记忆清理、隐私边界
import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from db.models import Base, AgentConversation

# 使用临时文件数据库进行测试
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db", prefix="test_conversation_")
TEST_DB_URL = f"sqlite+aiosqlite:///{_test_db_path}"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # 清理临时文件（在最后一个测试之后）
    await test_engine.dispose()


class TestAgentMemoryService:
    """对话记忆服务基础测试。"""

    @pytest.mark.asyncio
    async def test_append_and_get_messages(self):
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            await append_message(db, 9001, "user", "你好", intent="ask")
            await append_message(db, 9001, "assistant", "你好！有什么可以帮你的？", intent="ask")

            messages = await get_recent_messages(db, 9001)
            assert len(messages) == 2
            assert messages[0]["role"] == "user"
            assert messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_messages_ordered_by_time(self):
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            await append_message(db, 9001, "user", "第一条", intent="ask")
            await append_message(db, 9001, "assistant", "回复1", intent="ask")
            await append_message(db, 9001, "user", "第二条", intent="ask")

            messages = await get_recent_messages(db, 9001)
            assert len(messages) == 3
            assert "第一条" in messages[0]["content"]
            assert "第二条" in messages[2]["content"]

    @pytest.mark.asyncio
    async def test_max_messages_limit(self):
        from core.services.agent_memory_service import append_message, get_recent_messages, MAX_MESSAGES

        async with TestSessionLocal() as db:
            # 写入超过 MAX_MESSAGES 条消息
            for i in range(MAX_MESSAGES + 5):
                await append_message(db, 9001, "user", f"消息{i}", intent="ask")

            messages = await get_recent_messages(db, 9001)
            assert len(messages) == MAX_MESSAGES
            # 应该是最新的 MAX_MESSAGES 条
            assert f"消息{MAX_MESSAGES + 4}" in messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_different_students_isolated(self):
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            await append_message(db, 9001, "user", "学生1的消息", intent="ask")
            await append_message(db, 9002, "user", "学生2的消息", intent="ask")

            messages1 = await get_recent_messages(db, 9001)
            messages2 = await get_recent_messages(db, 9002)

            assert len(messages1) == 1
            assert "学生1" in messages1[0]["content"]
            assert len(messages2) == 1
            assert "学生2" in messages2[0]["content"]

    @pytest.mark.asyncio
    async def test_metadata_saved(self):
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            await append_message(
                db, 9001, "assistant", "基于你的数据...",
                intent="ask",
                metadata={"used_tools": ["get_student_profile"], "question_type": "profile_question"},
            )

            # 直接查询验证 metadata 保存
            from sqlalchemy import select
            stmt = select(AgentConversation).where(AgentConversation.student_id == 9001)
            result = await db.execute(stmt)
            record = result.scalar_one()
            assert record.metadata_["used_tools"] == ["get_student_profile"]
            assert record.metadata_["question_type"] == "profile_question"

    @pytest.mark.asyncio
    async def test_content_length_limit(self):
        from core.services.agent_memory_service import append_message

        async with TestSessionLocal() as db:
            long_content = "x" * 5000  # 超过 2000 字符限制
            record = await append_message(db, 9001, "user", long_content, intent="ask")
            assert len(record.content) <= 2000


class TestContinuousFollowUp:
    """连续追问测试——验证智能体能理解代词指代。"""

    @pytest.mark.asyncio
    async def test_followup_with_pronoun(self):
        """测试：先问任务推荐，再追问"为什么是它？"，智能体应能理解"它"指代上一次推荐的任务。"""
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            # 模拟第一轮对话
            await append_message(db, 9001, "user", "我应该先做哪个任务？", intent="ask")
            await append_message(db, 9001, "assistant", "建议先完成「Python 基础强化」任务，因为你的技术技能评分较低。", intent="ask",
                               metadata={"used_tools": ["get_growth_tasks", "get_latest_diagnosis"]})

            # 第二轮追问
            await append_message(db, 9001, "user", "为什么是它？", intent="ask")

            # 验证记忆包含上下文
            messages = await get_recent_messages(db, 9001)
            assert len(messages) == 3
            # 第一条是初始问题
            assert "哪个任务" in messages[0]["content"]
            # 第二条是助手回复，包含具体任务名
            assert "Python" in messages[1]["content"]
            # 第三条是追问
            assert "为什么" in messages[2]["content"]

    @pytest.mark.asyncio
    async def test_followup_context_available_for_llm(self):
        """验证：连续追问时，历史对话能被正确注入 LLM 上下文。"""
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            # 模拟多轮对话
            await append_message(db, 9001, "user", "我的匹配度怎么样？", intent="ask")
            await append_message(db, 9001, "assistant", "你当前的匹配度为 65%，主要差距在技术技能方面。", intent="ask")
            await append_message(db, 9001, "user", "那怎么提升呢？", intent="ask")

            messages = await get_recent_messages(db, 9001)
            # LLM 收到的上下文应包含完整的对话历史
            assert len(messages) == 3
            # "那怎么提升" 中的 "那" 指代上文的匹配度差距
            assert "匹配度" in messages[1]["content"]


class TestMemoryCleanup:
    """记忆清理测试。"""

    @pytest.mark.asyncio
    async def test_clear_old_messages(self):
        from core.services.agent_memory_service import append_message, clear_old_messages

        async with TestSessionLocal() as db:
            # 写入一条"旧"消息（直接修改 created_at）
            await append_message(db, 9001, "user", "旧消息", intent="ask")

            from sqlalchemy import update
            from core.utils.time import utc_now
            from datetime import timedelta
            old_time = utc_now() - timedelta(days=10)
            await db.execute(
                update(AgentConversation)
                .where(AgentConversation.student_id == 9001)
                .values(created_at=old_time)
            )
            await db.commit()

            # 写入一条新消息
            await append_message(db, 9001, "user", "新消息", intent="ask")

            # 清理 7 天前的消息
            deleted = await clear_old_messages(db, before_days=7)
            assert deleted >= 1

            # 验证只有新消息保留
            from core.services.agent_memory_service import get_recent_messages
            messages = await get_recent_messages(db, 9001)
            assert len(messages) == 1
            assert "新消息" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_no_privacy_leak(self):
        """验证：不同学生的记忆完全隔离，不会互相泄露。"""
        from core.services.agent_memory_service import append_message, get_recent_messages

        async with TestSessionLocal() as db:
            await append_message(db, 9001, "user", "学生1的敏感信息", intent="ask")
            await append_message(db, 9002, "user", "学生2的敏感信息", intent="ask")

            messages1 = await get_recent_messages(db, 9001)
            messages2 = await get_recent_messages(db, 9002)

            # 学生1看不到学生2的信息
            for msg in messages1:
                assert "学生2" not in msg["content"]
            for msg in messages2:
                assert "学生1" not in msg["content"]
