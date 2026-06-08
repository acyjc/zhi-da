# 测试 Skill Registry 和 Planner 升级
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.agent.skills import (
    AgentSkill, SkillRegistry, register_all_skills, get_skill_registry,
)
from core.agent.planner import StudentPlanner, StudentState, Plan
from core.agent.student_runtime import build_reasoning


class TestAgentSkillModel:
    """AgentSkill Pydantic 模型测试。"""

    def test_create_skill(self):
        skill = AgentSkill(
            name="test_skill",
            description="测试能力",
            allowed_intents=["diagnose"],
            tools=["get_student_profile"],
            risk_level="low",
        )
        assert skill.name == "test_skill"
        assert skill.risk_level == "low"
        assert skill.visible_to_user is True

    def test_skill_defaults(self):
        skill = AgentSkill(name="minimal", description="最简")
        assert skill.tools == []
        assert skill.allowed_intents == []
        assert skill.risk_level == "low"
        assert skill.output_schema == "AgentResult"


class TestSkillRegistry:
    """SkillRegistry 注册、查询和验证测试。"""

    def test_register_and_get(self):
        registry = SkillRegistry()
        skill = AgentSkill(name="test", description="测试", risk_level="low")
        registry.register(skill)
        assert registry.get("test") is not None
        assert registry.get("test").name == "test"

    def test_duplicate_register_raises(self):
        registry = SkillRegistry()
        skill = AgentSkill(name="dup", description="重复")
        registry.register(skill)
        with pytest.raises(ValueError, match="已注册"):
            registry.register(skill)

    def test_get_nonexistent_returns_none(self):
        registry = SkillRegistry()
        assert registry.get("nonexistent") is None

    def test_list_skills(self):
        registry = SkillRegistry()
        registry.register(AgentSkill(name="a", description="A"))
        registry.register(AgentSkill(name="b", description="B"))
        assert len(registry.list_skills()) == 2
        assert set(registry.list_skill_names()) == {"a", "b"}

    def test_get_skills_for_intent(self):
        registry = SkillRegistry()
        registry.register(AgentSkill(name="diag", description="诊断", allowed_intents=["diagnose"]))
        registry.register(AgentSkill(name="ask", description="问答", allowed_intents=["ask"]))
        registry.register(AgentSkill(name="both", description="两者", allowed_intents=["diagnose", "ask"]))
        diag_skills = registry.get_skills_for_intent("diagnose")
        assert len(diag_skills) == 2
        assert {s.name for s in diag_skills} == {"diag", "both"}

    def test_validate_skill_valid(self):
        registry = SkillRegistry()
        registry.register(AgentSkill(name="valid", description="合法", tools=[]))
        errors = registry.validate_skill("valid")
        assert errors == []

    def test_validate_skill_not_registered(self):
        registry = SkillRegistry()
        errors = registry.validate_skill("missing")
        assert len(errors) == 1
        assert "未注册" in errors[0]

    def test_validate_all(self):
        registry = SkillRegistry()
        registry.register(AgentSkill(name="ok", description="OK"))
        registry.register(AgentSkill(name="bad", description="Bad"))
        result = registry.validate_all()
        assert result == {}  # 没有提供 tool_registry，所以不会检查工具

    def test_get_skill_summary(self):
        registry = SkillRegistry()
        registry.register(AgentSkill(name="vis", description="可见", visible_to_user=True))
        registry.register(AgentSkill(name="hid", description="隐藏", visible_to_user=False))
        summary = registry.get_skill_summary()
        assert len(summary) == 1
        assert summary[0]["name"] == "vis"


class TestRegisterAllSkills:
    """首批 Skill 注册测试。"""

    def test_register_all(self):
        registry = SkillRegistry()
        register_all_skills(registry)
        names = registry.list_skill_names()
        assert "profile_completeness_check" in names
        assert "diagnose_student" in names
        assert "plan_growth_tasks" in names
        assert "review_task_evidence" in names
        assert "re_evaluate_student" in names
        assert "authorization_advice" in names
        assert "answer_student_question" in names
        assert "match_jobs" in names

    def test_all_skills_have_tools(self):
        registry = SkillRegistry()
        register_all_skills(registry)
        for skill in registry.list_skills():
            assert isinstance(skill.tools, list)
            # 每个 Skill 至少有一个工具
            assert len(skill.tools) >= 1, f"Skill '{skill.name}' 没有定义工具"

    def test_all_skills_have_intents(self):
        registry = SkillRegistry()
        register_all_skills(registry)
        for skill in registry.list_skills():
            assert len(skill.allowed_intents) >= 1, f"Skill '{skill.name}' 没有定义意图"

    def test_global_registry_singleton(self):
        r1 = get_skill_registry()
        r2 = get_skill_registry()
        assert r1 is r2


class TestStudentState:
    """StudentState 数据类测试。"""

    def test_defaults(self):
        state = StudentState()
        assert state.profile_completeness == 0.0
        assert state.is_complete is False
        assert state.has_diagnosis is False
        assert state.pending_tasks == 0
        assert state.completed_tasks == 0
        assert state.has_authorization is False


class TestPlannerSkillSelection:
    """Planner 状态驱动 Skill 选择测试。"""

    def test_select_skill_diagnose_incomplete(self):
        state = StudentState(is_complete=False, profile_completeness=0.5)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("diagnose", state, registry)
        assert skill == "profile_completeness_check"

    def test_select_skill_diagnose_complete(self):
        state = StudentState(is_complete=True, profile_completeness=0.9)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("diagnose", state, registry)
        assert skill == "diagnose_student"

    def test_select_skill_review_task(self):
        state = StudentState(is_complete=True)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("review_task", state, registry)
        assert skill == "review_task_evidence"

    def test_select_skill_re_evaluate(self):
        state = StudentState(is_complete=True)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("re_evaluate", state, registry)
        assert skill == "re_evaluate_student"

    def test_select_skill_continue_growth_no_diagnosis(self):
        state = StudentState(is_complete=True, has_diagnosis=False)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("continue_growth", state, registry)
        assert skill == "diagnose_student"

    def test_select_skill_continue_growth_with_diagnosis(self):
        state = StudentState(is_complete=True, has_diagnosis=True)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("continue_growth", state, registry)
        assert skill == "plan_growth_tasks"

    def test_select_skill_ask(self):
        state = StudentState(is_complete=True, has_diagnosis=True, pending_tasks=2)
        registry = get_skill_registry()
        skill = StudentPlanner._select_skill("ask", state, registry)
        assert skill == "answer_student_question"


class TestBuildReasoning:
    """build_reasoning 函数测试。"""

    def test_basic_reasoning(self):
        r = build_reasoning(
            basis=["学生信息完整"],
            decision="执行诊断",
            confidence=0.8,
        )
        assert r["basis"] == ["学生信息完整"]
        assert r["confidence"] == 0.8
        assert r["used_tools"] == []
        assert "selected_skill" not in r

    def test_reasoning_with_skill(self):
        r = build_reasoning(
            basis=["信息完整"],
            decision="诊断",
            confidence=0.9,
            selected_skill="diagnose_student",
        )
        assert r["selected_skill"] == "diagnose_student"

    def test_reasoning_confidence_clamped(self):
        r = build_reasoning(basis=[], decision="", confidence=1.5)
        assert r["confidence"] == 1.0
        r2 = build_reasoning(basis=[], decision="", confidence=-0.5)
        assert r2["confidence"] == 0.0

    def test_reasoning_with_tools_and_limits(self):
        r = build_reasoning(
            basis=["有诊断"],
            decision="成长任务",
            used_tools=["get_growth_tasks", "get_student_profile"],
            limits=["未验证附件"],
            selected_skill="plan_growth_tasks",
        )
        assert len(r["used_tools"]) == 2
        assert len(r["limits"]) == 1
        assert r["selected_skill"] == "plan_growth_tasks"
