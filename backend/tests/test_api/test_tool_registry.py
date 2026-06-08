# 工具注册表单元测试
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.agent.tools import ToolRegistry, ToolResult, register_all_tools
from core.agent.question_classifier import classify_question, QuestionType, QUESTION_TOOL_MAP


class TestToolResult:
    """ToolResult 数据类测试。"""

    def test_success_result(self):
        result = ToolResult(success=True, data={"name": "test"})
        assert result.success is True
        assert result.data == {"name": "test"}
        assert result.error == ""
        assert result.source == ""

    def test_error_result(self):
        result = ToolResult(success=False, error="not found")
        assert result.success is False
        assert result.data is None
        assert result.error == "not found"

    def test_default_values(self):
        result = ToolResult(success=True)
        assert result.data is None
        assert result.error == ""
        assert result.source == ""

    def test_source_field(self):
        result = ToolResult(success=True, data={}, source="get_profile")
        assert result.source == "get_profile"


class TestToolRegistry:
    """ToolRegistry 核心功能测试。"""

    def test_register_and_get(self):
        registry = ToolRegistry()
        registry.register("test_tool", "测试工具", {}, lambda: None)
        tool = registry.get("test_tool")
        assert tool is not None
        assert tool["name"] == "test_tool"
        assert tool["description"] == "测试工具"
        assert tool["read_only"] is True

    def test_register_duplicate_raises(self):
        registry = ToolRegistry()
        registry.register("tool1", "工具1", {}, lambda: None)
        with pytest.raises(ValueError, match="已注册"):
            registry.register("tool1", "工具2", {}, lambda: None)

    def test_get_nonexistent(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.register("tool_a", "工具A", {}, lambda: None)
        registry.register("tool_b", "工具B", {}, lambda: None)
        tools = registry.list_tools()
        assert len(tools) == 2
        names = [t["name"] for t in tools]
        assert "tool_a" in names
        assert "tool_b" in names

    def test_list_openai_tools(self):
        registry = ToolRegistry()
        registry.register(
            "get_profile", "获取学生画像",
            {"type": "object", "properties": {"student_id": {"type": "string"}}},
            lambda: None,
        )
        openai_tools = registry.list_openai_tools()
        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "get_profile"
        assert "parameters" in openai_tools[0]["function"]

    def test_call_tool_success(self):
        async def _test():
            async def mock_handler(db, student_id):
                return {"name": "张三", "grade": "大三"}

            registry = ToolRegistry()
            registry.register("get_profile", "获取学生画像", {}, mock_handler)
            result = await registry.call("get_profile", db=None, student_id=9001)
            assert result.success is True
            assert result.data == {"name": "张三", "grade": "大三"}
            assert result.source == "get_profile"

        asyncio.run(_test())

    def test_call_tool_error(self):
        async def _test():
            async def failing_handler(db, student_id):
                raise ValueError("学生不存在")

            registry = ToolRegistry()
            registry.register("get_profile", "获取学生画像", {}, failing_handler)
            result = await registry.call("get_profile", db=None, student_id=9999)
            assert result.success is False
            assert "学生不存在" in result.error
            assert result.source == "get_profile"

        asyncio.run(_test())

    def test_call_nonexistent_tool(self):
        async def _test():
            registry = ToolRegistry()
            result = await registry.call("nonexistent")
            assert result.success is False
            assert "未注册" in result.error
            assert result.source == "nonexistent"

        asyncio.run(_test())

    def test_register_write_tool(self):
        registry = ToolRegistry()
        registry.register("write_tool", "写工具", {}, lambda: None, read_only=False)
        tool = registry.get("write_tool")
        assert tool["read_only"] is False

    def test_is_tool_allowed_no_filter(self):
        """无 allowed_tools 过滤时，已注册工具均允许。"""
        registry = ToolRegistry()
        registry.register("tool_a", "工具A", {}, lambda: None)
        assert registry.is_tool_allowed("tool_a") is True
        assert registry.is_tool_allowed("tool_b") is False

    def test_is_tool_allowed_with_filter(self):
        """有 allowed_tools 过滤时，仅允许列表中的工具。"""
        registry = ToolRegistry(allowed_tools={"tool_a"})
        registry.register("tool_a", "工具A", {}, lambda: None)
        registry.register("tool_b", "工具B", {}, lambda: None)
        assert registry.is_tool_allowed("tool_a") is True
        assert registry.is_tool_allowed("tool_b") is False

    def test_validate_tool_suggestions(self):
        """验证 LLM 建议的工具列表，仅返回允许的工具。"""
        registry = ToolRegistry(allowed_tools={"tool_a", "tool_c"})
        registry.register("tool_a", "工具A", {}, lambda: None)
        registry.register("tool_b", "工具B", {}, lambda: None)
        registry.register("tool_c", "工具C", {}, lambda: None)
        valid = registry.validate_tool_suggestions(["tool_a", "tool_b", "tool_d"])
        assert valid == ["tool_a"]


class TestRegisterAllTools:
    """register_all_tools 工厂函数测试。"""

    def test_all_7_tools_registered(self):
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        tools = registry.list_tools()
        assert len(tools) == 7

        expected_names = {
            "get_student_profile", "get_latest_diagnosis", "get_diagnosis_history",
            "get_growth_tasks", "get_authorizations", "get_visible_jobs", "get_job_detail",
        }
        actual_names = {t["name"] for t in tools}
        assert actual_names == expected_names

    def test_all_tools_read_only(self):
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        for tool in registry.list_tools():
            assert tool["read_only"] is True, f"{tool['name']} should be read_only"

    def test_all_tools_have_description(self):
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        for tool in registry.list_tools():
            assert tool["description"], f"{tool['name']} missing description"

    def test_all_tools_have_parameters(self):
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        for tool in registry.list_tools():
            assert "parameters" in tool, f"{tool['name']} missing parameters"


class TestQuestionClassifier:
    """问题分类器测试。"""

    def test_profile_question(self):
        r = classify_question("我的技术技能怎么样？")
        assert r.question_type == QuestionType.PROFILE
        assert "get_student_profile" in r.required_tools

    def test_diagnosis_question(self):
        r = classify_question("为什么我的评分这么低？")
        assert r.question_type == QuestionType.DIAGNOSIS

    def test_growth_task_question(self):
        r = classify_question("我下一步做哪个任务？")
        assert r.question_type == QuestionType.GROWTH_TASK
        assert "get_growth_tasks" in r.required_tools

    def test_job_match_question(self):
        r = classify_question("有哪些适合我的岗位？")
        assert r.question_type == QuestionType.JOB_MATCH

    def test_authorization_question(self):
        r = classify_question("我授权了哪些企业？")
        assert r.question_type == QuestionType.AUTHORIZATION

    def test_unsupported_interview(self):
        r = classify_question("帮我模拟面试")
        assert r.question_type == QuestionType.UNSUPPORTED
        assert r.required_tools == []
        assert r.confidence >= 0.9

    def test_unsupported_resume(self):
        r = classify_question("帮我简历优化")
        assert r.question_type == QuestionType.UNSUPPORTED

    def test_unsupported_apply(self):
        r = classify_question("帮我投递简历")
        assert r.question_type == QuestionType.UNSUPPORTED

    def test_general_advice(self):
        r = classify_question("你好")
        assert r.question_type == QuestionType.GENERAL_ADVICE

    def test_general_advice_fallback(self):
        r = classify_question("今天天气怎么样？")
        assert r.question_type == QuestionType.GENERAL_ADVICE

    def test_empty_message(self):
        r = classify_question("")
        assert r.question_type == QuestionType.GENERAL_ADVICE
        assert r.confidence <= 0.5

    def test_classification_has_reason(self):
        r = classify_question("我的技能怎么样？")
        assert r.reason != ""

    def test_tool_map_consistency(self):
        """验证 QUESTION_TOOL_MAP 中每个类型的工具都在 ToolRegistry 中。"""
        mock_db = AsyncMock()
        registry = register_all_tools(mock_db, 9001)
        registered_names = {t["name"] for t in registry.list_tools()}

        for q_type, tools in QUESTION_TOOL_MAP.items():
            for tool_name in tools:
                assert tool_name in registered_names, f"{q_type} references unregistered tool {tool_name}"
