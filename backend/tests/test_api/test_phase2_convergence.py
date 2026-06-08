# Phase 2 收口阶段测试——验证 P0/P1/P2 任务完成情况
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC


# ========== Task 5: Intent-level tool filtering ==========
class TestIntentToolFiltering:
    """验证工具建议按 intent 过滤（P1-任务5）。"""

    def _make_registry(self):
        from core.agent.tools import ToolRegistry
        registry = ToolRegistry()
        registry.register(
            name="open_tool",
            description="所有 intent 可用",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=AsyncMock(),
            source="test",
        )
        registry.register(
            name="ask_only_tool",
            description="仅 ask 可用",
            parameters={"type": "object", "properties": {}, "required": []},
            handler=AsyncMock(),
            allowed_intents=["ask"],
            source="test",
        )
        return registry

    def test_validate_with_intent_approves_open_tool(self):
        registry = self._make_registry()
        result = registry.validate_tool_suggestions(["open_tool"], intent="diagnose")
        assert result == ["open_tool"]

    def test_validate_with_intent_rejects_ask_only_for_diagnose(self):
        registry = self._make_registry()
        result = registry.validate_tool_suggestions(["ask_only_tool"], intent="diagnose")
        assert result == []

    def test_validate_with_intent_allows_ask_only_for_ask(self):
        registry = self._make_registry()
        result = registry.validate_tool_suggestions(["ask_only_tool"], intent="ask")
        assert result == ["ask_only_tool"]

    def test_validate_without_intent_checks_global_only(self):
        registry = self._make_registry()
        result = registry.validate_tool_suggestions(["ask_only_tool"])
        assert result == ["ask_only_tool"]

    def test_validate_nonexistent_tool_rejected(self):
        registry = self._make_registry()
        result = registry.validate_tool_suggestions(["nonexistent"], intent="ask")
        assert result == []

    def test_get_rejected_tools_returns_reasons(self):
        registry = self._make_registry()
        rejected = registry.get_rejected_tools(["ask_only_tool", "nonexistent"], intent="diagnose")
        assert len(rejected) == 2
        names = [r["name"] for r in rejected]
        assert "ask_only_tool" in names
        assert "nonexistent" in names
        # 检查拒绝原因
        for r in rejected:
            assert "reason" in r
            assert r["reason"]  # 非空

    def test_get_rejected_tools_empty_when_all_approved(self):
        registry = self._make_registry()
        rejected = registry.get_rejected_tools(["open_tool"], intent="ask")
        assert rejected == []


# ========== Task 4: Memory summary wiring ==========
class TestMemorySummaryWiring:
    """验证各 intent 的 memory summary 写入（P1-任务4）。"""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_diagnose_summary_content(self, mock_db):
        """diagnose 摘要应包含版本和匹配度。"""
        from core.services.agent_memory_service import maybe_write_memory
        await maybe_write_memory(
            mock_db, 9001, "diagnose",
            summary="诊断完成 v2，匹配度75%，主要短板: tech_skills",
            metadata={"version": 2, "match_score": 0.75},
        )
        mock_db.add.assert_called_once()
        record = mock_db.add.call_args[0][0]
        assert record.role == "system_summary"
        assert record.intent == "diagnose"
        assert "v2" in record.content
        assert "75%" in record.content

    @pytest.mark.asyncio
    async def test_continue_growth_summary_content(self, mock_db):
        """continue_growth 摘要应包含进度信息。"""
        from core.services.agent_memory_service import maybe_write_memory
        await maybe_write_memory(
            mock_db, 9001, "continue_growth",
            summary="成长进度: 3/8 任务已完成，当前最优先: Python 基础练习",
            metadata={"completed": 3, "total": 8},
        )
        mock_db.add.assert_called_once()
        record = mock_db.add.call_args[0][0]
        assert record.role == "system_summary"
        assert record.intent == "continue_growth"
        assert "3/8" in record.content

    @pytest.mark.asyncio
    async def test_review_task_summary_content(self, mock_db):
        """review_task 摘要应包含任务 ID 和审核状态。"""
        from core.services.agent_memory_service import maybe_write_memory
        await maybe_write_memory(
            mock_db, 9001, "review_task",
            summary="任务 task1 审核通过",
            metadata={"task_id": "task1", "approved": True},
        )
        mock_db.add.assert_called_once()
        record = mock_db.add.call_args[0][0]
        assert record.role == "system_summary"
        assert record.intent == "review_task"
        assert "task1" in record.content

    @pytest.mark.asyncio
    async def test_re_evaluate_summary_content(self, mock_db):
        """re_evaluate 摘要应包含版本和能力变化。"""
        from core.services.agent_memory_service import maybe_write_memory
        await maybe_write_memory(
            mock_db, 9001, "re_evaluate",
            summary="复评完成 v3，匹配度80%，能力变化: tech: +5.0",
            metadata={"version": 3, "task_id": "task1", "match_score": 0.80},
        )
        mock_db.add.assert_called_once()
        record = mock_db.add.call_args[0][0]
        assert record.role == "system_summary"
        assert record.intent == "re_evaluate"
        assert "v3" in record.content

    @pytest.mark.asyncio
    async def test_navigate_does_not_write(self, mock_db):
        """navigate 不应写入记忆。"""
        from core.services.agent_memory_service import maybe_write_memory
        await maybe_write_memory(
            mock_db, 9001, "navigate",
            summary="不应写入",
        )
        mock_db.add.assert_not_called()


# ========== Warnings cleanup verification ==========
class TestWarningsCleanup:
    """验证 warnings 清理（P2-任务8）。"""

    def test_utc_now_is_timezone_aware(self):
        from core.utils.time import utc_now
        now = utc_now()
        assert now.tzinfo is not None

    def test_models_utc_now_helper(self):
        from db.models import _utc_now
        now = _utc_now()
        assert now.tzinfo is not None
        assert now.tzinfo == UTC

    def test_job_response_uses_configdict(self):
        from core.models.job import JobResponse
        assert hasattr(JobResponse, "model_config")
