# Skill Registry——管理智能体可调用的高层能力单元
# Skill 是 Agent 的"可调用能力"，每个 Skill 绑定一组 Tool，由 Planner 选择、Runtime 执行。
from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---- Skill 数据模型 ----

class AgentSkill(BaseModel):
    """Agent 能力单元定义。

    每个 Skill 代表 Agent 可以完成的一项高层能力，例如"诊断学生""审核任务证据"。
    Skill 与 Tool 的关系：Skill 是目的，Tool 是手段。
    """
    name: str = Field(description="Skill 唯一名称，使用 snake_case")
    description: str = Field(description="Skill 功能描述，用于 Planner 决策和前端展示")
    allowed_intents: list[str] = Field(
        default_factory=list,
        description="允许触发此 Skill 的意图列表",
    )
    required_context: list[str] = Field(
        default_factory=list,
        description="执行此 Skill 前必须可用的上下文信息",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="此 Skill 执行时需要调用的工具名称列表",
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        default="low",
        description="风险等级：low=只读建议, medium=会修改数据, high=涉及授权或不可逆操作",
    )
    output_schema: str = Field(
        default="AgentResult",
        description="输出格式标识，用于前端解析",
    )
    visible_to_user: bool = Field(
        default=True,
        description="是否在用户可见的 reasoning 中展示此 Skill",
    )


# ---- Skill Registry ----

class SkillRegistry:
    """Skill 注册表——管理所有可用 Skill 的注册、查询和验证。

    用法:
        registry = SkillRegistry()
        register_all_skills(registry)
        skill = registry.get("diagnose_student")
        assert skill is not None
    """

    def __init__(self) -> None:
        self._skills: dict[str, AgentSkill] = {}

    def register(self, skill: AgentSkill) -> None:
        """注册一个 Skill。

        Raises:
            ValueError: Skill 名称已存在。
        """
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' 已注册，不允许重复注册")
        self._skills[skill.name] = skill
        logger.debug("注册 Skill: %s (风险=%s, 工具=%s)", skill.name, skill.risk_level, skill.tools)

    def get(self, name: str) -> AgentSkill | None:
        """获取指定 Skill，不存在返回 None。"""
        return self._skills.get(name)

    def list_skills(self) -> list[AgentSkill]:
        """返回所有已注册 Skill 列表。"""
        return list(self._skills.values())

    def list_skill_names(self) -> list[str]:
        """返回所有已注册 Skill 名称列表。"""
        return list(self._skills.keys())

    def get_skills_for_intent(self, intent: str) -> list[AgentSkill]:
        """返回允许在指定意图下使用的 Skill 列表。"""
        return [
            s for s in self._skills.values()
            if intent in s.allowed_intents
        ]

    def validate_skill(self, name: str, tool_registry=None) -> list[str]:
        """验证 Skill 的合法性，返回问题列表（空列表表示合法）。

        检查项：
        - Skill 是否存在
        - Skill 引用的 Tool 是否都已注册（如果提供 tool_registry）
        """
        errors = []
        skill = self._skills.get(name)
        if not skill:
            errors.append(f"Skill '{name}' 未注册")
            return errors

        if tool_registry is not None:
            for tool_name in skill.tools:
                if tool_registry.get(tool_name) is None:
                    errors.append(
                        f"Skill '{name}' 引用了未注册的工具 '{tool_name}'"
                    )

        return errors

    def validate_all(self, tool_registry=None) -> dict[str, list[str]]:
        """验证所有 Skill，返回 {skill_name: [errors]} 字典。"""
        result = {}
        for name in self._skills:
            errors = self.validate_skill(name, tool_registry)
            if errors:
                result[name] = errors
        return result

    def get_skill_summary(self) -> list[dict]:
        """返回 Skill 清单摘要（用于 system prompt 或前端展示）。"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "risk_level": s.risk_level,
                "tools": s.tools,
            }
            for s in self._skills.values()
            if s.visible_to_user
        ]


# ---- 首批核心 Skill 注册 ----

def register_all_skills(registry: SkillRegistry) -> None:
    """注册第一批核心 Skill。

    Skill 清单：
    | Skill                        | 作用                      | 风险   |
    |------------------------------|--------------------------|--------|
    | profile_completeness_check   | 判断学生信息是否足够诊断    | low    |
    | diagnose_student             | 运行能力诊断               | medium |
    | match_jobs                   | 基于已审核岗位做匹配        | low    |
    | plan_growth_tasks            | 生成或读取成长任务          | medium |
    | review_task_evidence         | 审核任务证据               | medium |
    | re_evaluate_student          | 基于成长证据触发复评        | medium |
    | authorization_advice         | 给出授权建议或引导          | low    |
    | answer_student_question      | 基于上下文回答学生问题       | low    |
    """

    registry.register(AgentSkill(
        name="profile_completeness_check",
        description="检查学生档案信息完整度，判断是否可以进行诊断",
        allowed_intents=["diagnose"],
        required_context=["student_profile"],
        tools=["get_student_profile"],
        risk_level="low",
        output_schema="CompletenessCheckResult",
    ))

    registry.register(AgentSkill(
        name="diagnose_student",
        description="运行五维能力诊断 Pipeline，生成能力画像和岗位匹配",
        allowed_intents=["diagnose"],
        required_context=["student_profile", "completeness_check_passed"],
        tools=["get_student_profile", "get_latest_diagnosis", "get_visible_jobs"],
        risk_level="medium",
        output_schema="DiagnosisResult",
    ))

    registry.register(AgentSkill(
        name="match_jobs",
        description="基于学生能力画像和已审核岗位进行匹配分析",
        allowed_intents=["diagnose", "ask"],
        required_context=["diagnosis_result"],
        tools=["get_student_profile", "get_latest_diagnosis", "get_visible_jobs"],
        risk_level="low",
        output_schema="MatchResult",
    ))

    registry.register(AgentSkill(
        name="plan_growth_tasks",
        description="读取或生成学生成长任务，推进成长路径",
        allowed_intents=["continue_growth", "diagnose"],
        required_context=["diagnosis_result"],
        tools=["get_student_profile", "get_latest_diagnosis", "get_growth_tasks"],
        risk_level="medium",
        output_schema="GrowthTaskResult",
    ))

    registry.register(AgentSkill(
        name="review_task_evidence",
        description="审核学生提交的任务证据，判定通过或未通过",
        allowed_intents=["review_task"],
        required_context=["growth_task", "evidence"],
        tools=["get_student_profile", "get_growth_tasks"],
        risk_level="medium",
        output_schema="ReviewResult",
    ))

    registry.register(AgentSkill(
        name="re_evaluate_student",
        description="基于成长任务完成证据触发复评，量化能力提升",
        allowed_intents=["re_evaluate"],
        required_context=["diagnosis_result", "completed_task"],
        tools=["get_student_profile", "get_latest_diagnosis", "get_growth_tasks"],
        risk_level="medium",
        output_schema="ReEvaluationResult",
    ))

    registry.register(AgentSkill(
        name="authorization_advice",
        description="给出企业授权建议，引导学生完成授权操作",
        allowed_intents=["ask", "navigate"],
        required_context=["student_profile"],
        tools=["get_student_profile", "get_authorizations", "get_visible_jobs"],
        risk_level="low",
        output_schema="AuthorizationAdvice",
    ))

    registry.register(AgentSkill(
        name="answer_student_question",
        description="基于学生上下文回答职业成长相关问题",
        allowed_intents=["ask"],
        required_context=["student_profile"],
        tools=[
            "get_student_profile",
            "get_latest_diagnosis",
            "get_diagnosis_history",
            "get_growth_tasks",
            "get_authorizations",
            "get_visible_jobs",
        ],
        risk_level="low",
        output_schema="AdviceResult",
    ))


# ---- 模块级便捷函数 ----

_default_registry: SkillRegistry | None = None


def get_skill_registry() -> SkillRegistry:
    """获取全局 SkillRegistry 单例（懒加载）。"""
    global _default_registry
    if _default_registry is None:
        _default_registry = SkillRegistry()
        register_all_skills(_default_registry)
    return _default_registry
