# 再诊断流程——根据变化的维度动态构建步骤列表，仅刷新受影响的部分
from core.pipelines.diagnosis_pipeline import ProfileStep, MatchStep, GapStep, PathStep, AdviceStep


def build_re_evaluate_pipeline(changed_dimensions: list[str]) -> list:
    steps = []
    profile_dimensions = [
        "tech_skills",
        "project_exp",
        "soft_skills",
        "domain_knowledge",
        "academic_foundation",
        "soft_skill_evidence",
    ]
    if any(d in changed_dimensions for d in profile_dimensions):
        steps.append(ProfileStep())
        steps.append(MatchStep())
        steps.append(GapStep())
    if any(d in changed_dimensions for d in ["tech_skills", "domain_knowledge", "academic_foundation"]):
        steps.append(PathStep())
    steps.append(AdviceStep())
    return steps
