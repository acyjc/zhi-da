# 测试 Agent Trace 服务
import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from db.models import Base, Student, AgentTrace
from core.services.agent_trace_service import (
    write_trace, get_traces_by_student, get_trace_by_request_id, TraceTimer,
)


@pytest.fixture
async def temp_db_session():
    """创建临时 SQLite 数据库并返回 session factory。"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield session_factory

    await engine.dispose()
    os.unlink(path)


@pytest.mark.asyncio
class TestAgentTraceService:
    """Agent Trace 写入和查询测试。"""

    async def test_write_and_query_trace(self, temp_db_session):
        async with temp_db_session() as session:
            # 先创建学生
            student = Student(id=9010, name="测试学生", grade="2023", major="CS", target_job="后端")
            session.add(student)
            await session.commit()

            # 写入 trace
            trace = await write_trace(
                session,
                request_id="req_test_001",
                student_id=9010,
                intent="diagnose",
                selected_skill="diagnose_student",
                used_tools=["get_student_profile", "get_latest_diagnosis"],
                output_action="diagnosis_completed",
                confidence=0.85,
                limits=["岗位匹配基于系统内可用岗位"],
                duration_ms=1500,
            )
            assert trace.request_id == "req_test_001"
            assert trace.selected_skill == "diagnose_student"

            # 查询 trace
            traces = await get_traces_by_student(session, 9010)
            assert len(traces) == 1
            assert traces[0]["selected_skill"] == "diagnose_student"
            assert traces[0]["confidence"] == 0.85

            # 按 request_id 查询
            trace_by_req = await get_trace_by_request_id(session, "req_test_001")
            assert trace_by_req is not None
            assert trace_by_req["intent"] == "diagnose"

    async def test_multiple_traces_ordered(self, temp_db_session):
        async with temp_db_session() as session:
            student = Student(id=9020, name="测试学生2", grade="2023", major="CS", target_job="前端")
            session.add(student)
            await session.commit()

            # 写入多条 trace
            for i in range(3):
                await write_trace(
                    session,
                    request_id=f"req_multi_{i}",
                    student_id=9020,
                    intent="ask",
                    selected_skill="answer_student_question",
                    confidence=0.5 + i * 0.1,
                )

            traces = await get_traces_by_student(session, 9020, limit=10)
            assert len(traces) == 3
            # 按时间倒序，最新的在前
            confidences = [t["confidence"] for t in traces]
            assert confidences == sorted(confidences, reverse=True)

    async def test_nonexistent_trace(self, temp_db_session):
        async with temp_db_session() as session:
            result = await get_trace_by_request_id(session, "nonexistent")
            assert result is None


class TestTraceTimer:
    """TraceTimer 计时器测试。"""

    def test_elapsed_zero_before_start(self):
        timer = TraceTimer()
        assert timer.elapsed_ms() == 0

    def test_elapsed_positive_after_start(self):
        import time
        timer = TraceTimer()
        timer.start()
        time.sleep(0.05)  # 50ms (Windows 精度较低，留足余量)
        assert timer.elapsed_ms() >= 10
