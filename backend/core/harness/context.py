# ContextBuilder — 组装 System Prompt + 用户上下文，注入领域约束防御 Prompt 注入
from .step import PipelineState


# 全局 System Prompt，定义 AI 角色和领域边界
SYSTEM_PROMPT = """你是一个专业的人才培养与职业规划 AI 助手。你的职责是：
1. 分析学生的技术能力、项目经验、软技能和领域知识
2. 评估学生与目标岗位的匹配度
3. 生成个性化的成长路径和建议

领域约束：
- 你只能回答与人才培养、职业规划、技能提升相关的问题
- 你的输出必须严格遵循指定的 JSON Schema 格式
- 你的评分必须在 0-100 范围内（或 0-1 范围内表示匹配度）
- 你的建议必须具体、可执行、可量化"""


class ContextBuilder:
    @staticmethod
    def build_system_prompt() -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}]

    @staticmethod
    def build_user_prompt(state: PipelineState, task_description: str, additional_context: str = "") -> list[dict]:
        messages = ContextBuilder.build_system_prompt()
        user_content = f"{task_description}\n\n当前上下文:\n"
        if state.input:
            user_content += f"学生信息: {state.input}\n"
        if additional_context:
            user_content += f"补充信息: {additional_context}\n"
        if state.results:
            relevant = {k: v for k, v in state.results.items() if k in ["profile", "match_result", "gap_analysis"]}
            if relevant:
                user_content += f"前置分析结果: {relevant}\n"
        messages.append({"role": "user", "content": user_content})
        return messages
