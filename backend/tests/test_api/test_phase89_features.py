# Phase 8/9 功能测试——工具治理、Planner安全、记忆策略、Deprecated 头、可解释性
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.agent.tools import ToolRegistry, ToolResult, register_all_tools
from core.agent.planner import StudentPlanner, NAVIGATE_TARGET_WHITELIST, EVIDENCE_MAX_LENGTH
from core.agent.student_runtime import build_reasoning


# ========================================
# Phase 8.1: 工具调用治理
# ========================================

class TestToolGovernance:
    """验证工具 schema 完整化（source、allowed_intents、参数校验）。"""

    def test_tool_has_source_field(self):
        """所有注册工具必须包含 source 字段。"""
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        for tool in registry.list_tools():
            assert "source" in tool, f"{tool['name']} missing source field"
            assert tool["source"], f"{tool['name']} has empty source"

    def test_is_tool_allowed_for_intent(self):
        """验证 allowed_intents 限制生效。"""
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        # get_job_detail 只允许 ask 意图
        assert registry.is_tool_allowed_for_intent("get_job_detail", "ask") is True
        assert registry.is_tool_allowed_for_intent("get_job_detail", "diagnose") is False
        # get_student_profile 不限制意图
        assert registry.is_tool_allowed_for_intent("get_student_profile", "ask") is True
        assert registry.is_tool_allowed_for_intent("get_student_profile", "diagnose") is True

    async def test_tool_parameter_validation(self):
        """工具调用缺少必要参数时应返回错误。"""
        registry = ToolRegistry()
        async def _dummy_handler(**kwargs):
            return {"ok": True}
        registry.register(
            name="test_tool",
            description="test",
            parameters={"type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]},
            handler=_dummy_handler,
        )
        # 缺少 student_id
        result = await registry.call("test_tool")
        assert result.success is False
        assert "缺少必要参数" in result.error

        # 空字符串 student_id
        result2 = await registry.call("test_tool", student_id="")
        assert result2.success is False

    async def test_tool_call_success(self):
        """正常参数应成功调用。"""
        registry = ToolRegistry()
        async def _dummy_handler(**kwargs):
            return {"data": "ok"}
        registry.register(
            name="test_tool",
            description="test",
            parameters={"type": "object", "properties": {"student_id": {"type": "string"}}, "required": ["student_id"]},
            handler=_dummy_handler,
        )
        result = await registry.call("test_tool", student_id=9001)
        assert result.success is True
        assert result.data == {"data": "ok"}


# ========================================
# Phase 6.2/8.2: Planner 安全校验
# ========================================

class TestPlannerSecurity:
    """验证 Planner 安全增强（证据格式、导航白名单、消息截断）。"""

    async def test_review_task_evidence_too_long(self):
        """超长证据应在 Planner 层被拒绝。"""
        ctx = {"id": 9005, "name": "test"}
        long_evidence = "a" * (EVIDENCE_MAX_LENGTH + 1)
        plan = await StudentPlanner.plan(ctx, "review_task", {"task_id": "t1", "evidence": long_evidence})
        assert plan.action == "error"
        assert "最大长度" in plan.reason

    async def test_review_task_evidence_just_right(self):
        """合法长度证据应通过 Planner。"""
        ctx = {"id": 9005, "name": "test"}
        evidence = "我完成了FastAPI教程学习"
        plan = await StudentPlanner.plan(ctx, "review_task", {"task_id": "t1", "evidence": evidence})
        assert plan.action == "review_task"

    async def test_navigate_invalid_target(self):
        """非法导航目标应被拒绝。"""
        ctx = {"id": 9005, "name": "test"}
        plan = await StudentPlanner.plan(ctx, "navigate", {"target": "admin_panel"})
        assert plan.action == "error"
        assert "不支持的导航目标" in plan.reason

    async def test_navigate_valid_target(self):
        """合法导航目标应通过。"""
        ctx = {"id": 9005, "name": "test"}
        for target in NAVIGATE_TARGET_WHITELIST:
            plan = await StudentPlanner.plan(ctx, "navigate", {"target": target})
            assert plan.action == "navigate", f"target={target} should be allowed"

    async def test_ask_message_truncated(self):
        """超长 ask 消息应被截断。"""
        ctx = {"id": 9005, "name": "test"}
        long_msg = "x" * 1500
        payload = {"message": long_msg}
        plan = await StudentPlanner.plan(ctx, "ask", payload)
        assert plan.action == "ask"
        assert len(payload["message"]) == 1000


# ========================================
# Phase 8.3: 可解释性标准
# ========================================

class TestReasoningStandard:
    """验证 build_reasoning 生成统一结构。"""

    def test_build_reasoning_structure(self):
        r = build_reasoning(
            basis=["学生信息"],
            decision="执行诊断",
            confidence=0.8,
            used_tools=["get_student_profile"],
            limits=["数据有限"],
        )
        assert "basis" in r
        assert "decision" in r
        assert "confidence" in r
        assert "used_tools" in r
        assert "limits" in r
        assert r["confidence"] == 0.8

    def test_confidence_clamped(self):
        """置信度应在 0.0-1.0 范围内。"""
        r = build_reasoning(basis=[], decision="", confidence=1.5)
        assert r["confidence"] == 1.0

        r2 = build_reasoning(basis=[], decision="", confidence=-0.5)
        assert r2["confidence"] == 0.0

    def test_defaults(self):
        """默认 used_tools 和 limits 为空列表。"""
        r = build_reasoning(basis=["test"], decision="test")
        assert r["used_tools"] == []
        assert r["limits"] == []


# ========================================
# Phase 6.4: 统一记忆策略
# ========================================

class TestMemoryPolicy:
    """验证记忆策略配置。"""

    def test_policy_ask_writes_full(self):
        from core.services.agent_memory_service import MEMORY_POLICY
        assert MEMORY_POLICY["ask"]["write"] is True
        assert MEMORY_POLICY["ask"]["mode"] == "full"

    def test_policy_diagnose_writes_summary(self):
        from core.services.agent_memory_service import MEMORY_POLICY
        assert MEMORY_POLICY["diagnose"]["write"] is True
        assert MEMORY_POLICY["diagnose"]["mode"] == "summary"

    def test_policy_navigate_does_not_write(self):
        from core.services.agent_memory_service import MEMORY_POLICY
        assert MEMORY_POLICY["navigate"]["write"] is False

    def test_policy_all_intents_covered(self):
        """所有 6 个意图都应有记忆策略定义。"""
        from core.services.agent_memory_service import MEMORY_POLICY
        expected_intents = {"ask", "diagnose", "continue_growth", "review_task", "re_evaluate", "navigate"}
        assert set(MEMORY_POLICY.keys()) == expected_intents
