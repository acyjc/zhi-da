# 诊断 Pipeline 定义——包含 5 个 PipelineStep，按序执行初诊流程
from core.harness.step import PipelineStep, PipelineState
from core.harness.context import ContextBuilder
from core.harness.validator import SchemaValidator
from core.harness.llm import get_llm_client
import json


# 能力画像步骤
class ProfileStep(PipelineStep):
    def __init__(self, name="profile", depends_on=None):
        super().__init__(name, depends_on)

    async def execute(self, state: PipelineState) -> PipelineState:
        llm = get_llm_client()
        student_info = state.input
        messages = ContextBuilder.build_user_prompt(state,
                "请基于以下学生信息生成四维能力画像。输出严格JSON格式，含 tech_skills, project_exp, soft_skills, domain_knowledge 四个维度，每项包含 weight 和 sub_items (含name, score(0-100), level)。",
                f"学生简历: {student_info.get('resume_text', '')} 技能: {student_info.get('tech_skills', {})} 软技能: {student_info.get('soft_skills', {})} 领域: {student_info.get('domain_knowledge', {})}")
        response = await llm.complete(messages)
        data, error = SchemaValidator.validate_json_output(response.content)
        if data and not error:
            data = SchemaValidator.validate_ability_scores(data)
            state.set("profile", data)
        else:
            state.set("profile", {
                "tech_skills": {"weight": 0.35, "sub_items": [{"name": k, "score": v, "level": "了解"} for k, v in student_info.get("tech_skills", {}).items()]},
                "project_exp": {"weight": 0.25, "sub_items": []},
                "soft_skills": {"weight": 0.20, "sub_items": [{"name": k, "score": v, "level": "了解"} for k, v in student_info.get("soft_skills", {}).items()]},
                "domain_knowledge": {"weight": 0.20, "sub_items": [{"name": k, "score": v, "level": "了解"} for k, v in student_info.get("domain_knowledge", {}).items()]},
            })
        return state


# 岗位匹配步骤
class MatchStep(PipelineStep):
    def __init__(self, name="match", depends_on=None):
        super().__init__(name, depends_on)

    async def execute(self, state: PipelineState) -> PipelineState:
        llm = get_llm_client()
        target_job = state.input.get("target_job", "")
        messages = ContextBuilder.build_user_prompt(state,
                f"学生目标岗位是「{target_job}」。请基于能力画像计算与5个岗位的匹配度。输出严格JSON: {{match_score: 0-1浮点数, dimension_scores: {{tech, project, soft, domain}}: 0-1浮点数, top5_jobs: [{{job_id, title, score, company}}], gap_details: [{{dimension, skill, current:0-100, required:0-100, gap}}]}}")
        response = await llm.complete(messages)
        data, error = SchemaValidator.validate_json_output(response.content)
        if data and not error:
            ms = data.get("match_score", 0)
            data["match_score"] = SchemaValidator.validate_match_score(ms)
            state.set("match_result", data)
        else:
            state.set("match_result", {"match_score": 0.5, "dimension_scores": {"tech": 0.5, "project": 0.5, "soft": 0.5, "domain": 0.5}, "top5_jobs": [], "gap_details": []})
        return state


# 差距分析步骤
class GapStep(PipelineStep):
    def __init__(self, name="gap", depends_on=None):
        super().__init__(name, depends_on)

    async def execute(self, state: PipelineState) -> PipelineState:
        match_result = state.get("match_result", {})
        gap_details = match_result.get("gap_details", [])
        state.set("gap_analysis", {"gaps": gap_details, "total_gaps": len(gap_details)})
        return state


# 成长路径规划步骤
class PathStep(PipelineStep):
    def __init__(self, name="path", depends_on=None):
        super().__init__(name, depends_on)

    async def execute(self, state: PipelineState) -> PipelineState:
        llm = get_llm_client()
        gaps = state.get("gap_analysis", {}).get("gaps", [])
        messages = ContextBuilder.build_user_prompt(state,
                "请基于差距分析结果，生成个性化成长路径。输出严格JSON: {phases: [{goal, weeks: 数字, tasks: [{name, description, resources: [链接], criteria}]}]}，包含2-3个阶段。",
                f"差距: {json.dumps(gaps, ensure_ascii=False)}")
        response = await llm.complete(messages)
        data, error = SchemaValidator.validate_json_output(response.content)
        if data and not error:
            state.set("growth_path", data)
        else:
            state.set("growth_path", {"phases": [{"goal": "基础能力提升", "weeks": 4, "tasks": [{"name": "夯实基础", "description": "针对薄弱技能进行专项练习", "resources": [], "criteria": "技能评分达到70+"}]}]})
        return state


# 职业建议生成步骤
class AdviceStep(PipelineStep):
    def __init__(self, name="advice", depends_on=None):
        super().__init__(name, depends_on)

    async def execute(self, state: PipelineState) -> PipelineState:
        llm = get_llm_client()
        messages = ContextBuilder.build_user_prompt(state,
                "请基于学生的能力画像和岗位匹配结果，生成职业发展建议和就业指导。输出严格JSON: {career_advice: 文本, recommended_directions: [方向], ai_reasoning: {每个建议的推理依据和置信度}}")
        response = await llm.complete(messages)
        data, error = SchemaValidator.validate_json_output(response.content)
        if data and not error:
            state.set("career_advice", data.get("career_advice", ""))
            state.set("ai_reasoning", data.get("ai_reasoning", {}))
        else:
            state.set("career_advice", "建议持续关注行业趋势，针对目标岗位持续提升核心技能。")
            state.set("ai_reasoning", {"note": "基于能力画像的通用建议"})
        return state
