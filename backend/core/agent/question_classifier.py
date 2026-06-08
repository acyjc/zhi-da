# 问题分类器——根据用户问题判断需要查询哪些上下文工具
from enum import Enum
from dataclasses import dataclass, field


class QuestionType(str, Enum):
    """问题类型枚举。"""
    PROFILE = "profile_question"
    DIAGNOSIS = "diagnosis_question"
    GROWTH_TASK = "growth_task_question"
    JOB_MATCH = "job_match_question"
    AUTHORIZATION = "authorization_question"
    GENERAL_ADVICE = "general_advice"
    UNSUPPORTED = "unsupported_request"


# 问题类型到工具的映射
QUESTION_TOOL_MAP: dict[QuestionType, list[str]] = {
    QuestionType.PROFILE: ["get_student_profile"],
    QuestionType.DIAGNOSIS: ["get_latest_diagnosis", "get_diagnosis_history"],
    QuestionType.GROWTH_TASK: ["get_growth_tasks", "get_latest_diagnosis"],
    QuestionType.JOB_MATCH: ["get_latest_diagnosis", "get_visible_jobs"],
    QuestionType.AUTHORIZATION: ["get_authorizations", "get_visible_jobs"],
    QuestionType.GENERAL_ADVICE: ["get_student_profile", "get_latest_diagnosis", "get_growth_tasks"],
    QuestionType.UNSUPPORTED: [],
}


@dataclass
class ClassificationResult:
    """分类结果。"""
    question_type: QuestionType
    required_tools: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reason: str = ""


# 关键词规则表
_KEYWORD_RULES: list[tuple[list[str], QuestionType]] = [
    # 不支持的功能（优先匹配）
    (["模拟面试", "面试模拟", "帮我面试"], QuestionType.UNSUPPORTED),
    (["投递简历", "自动投递", "帮我投"], QuestionType.UNSUPPORTED),
    (["简历优化", "简历重写", "改简历"], QuestionType.UNSUPPORTED),
    (["薪资谈判", "谈薪资"], QuestionType.UNSUPPORTED),
    (["即时聊天", "IM", "在线客服"], QuestionType.UNSUPPORTED),

    # 授权相关
    (["授权", "企业看到", "谁能看", "谁可以看到", "取消授权", "撤回授权"], QuestionType.AUTHORIZATION),

    # 岗位匹配
    (["匹配", "岗位", "推荐岗位", "适合我", "哪些岗位", "就业推荐", "找工作"], QuestionType.JOB_MATCH),

    # 成长任务
    (["任务", "下一步做", "成长路径", "学习计划", "怎么提升", "先做哪个", "任务进度", "完成任务"], QuestionType.GROWTH_TASK),

    # 诊断相关
    (["诊断", "匹配度", "为什么低", "分数", "评分", "能力分", "差距", "不足", "弱点", "短板"], QuestionType.DIAGNOSIS),

    # 画像相关
    (["画像", "技能", "能力画像", "我的技能", "技术栈", "项目经验", "软技能"], QuestionType.PROFILE),
]


def classify_question(message: str) -> ClassificationResult:
    """基于关键词规则分类用户问题。

    优先匹配不支持的功能，然后按关键词匹配具体类型，
    最后默认为通用建议。
    """
    if not message or not message.strip():
        return ClassificationResult(
            question_type=QuestionType.GENERAL_ADVICE,
            required_tools=QUESTION_TOOL_MAP[QuestionType.GENERAL_ADVICE],
            confidence=0.3,
            reason="空问题，默认为通用建议",
        )

    text = message.strip()

    # 按规则优先级匹配
    for keywords, q_type in _KEYWORD_RULES:
        for kw in keywords:
            if kw in text:
                return ClassificationResult(
                    question_type=q_type,
                    required_tools=QUESTION_TOOL_MAP[q_type],
                    confidence=0.8 if q_type != QuestionType.UNSUPPORTED else 0.9,
                    reason=f"关键词匹配: {kw}",
                )

    # 默认：通用建议
    return ClassificationResult(
        question_type=QuestionType.GENERAL_ADVICE,
        required_tools=QUESTION_TOOL_MAP[QuestionType.GENERAL_ADVICE],
        confidence=0.5,
        reason="无明确关键词，默认为通用建议",
    )
