# ORM 模型定义——Student/Job/DiagnosisResult/TaskProgress/GrowthRecord 五张核心表
#
# === 数据模型主次关系（Phase 9.2 数据治理）===
# 主模型（Primary）：新代码应优先使用
#   - Student         → 学生基本信息
#   - DiagnosisResult → 诊断结果（含版本管理）
#   - GrowthTask      → 成长任务（新版，绑定差距与预期影响）
#   - JobPost         → 企业岗位（三端统一）
#   - JobAbilityModel → 岗位能力模型
#   - Enterprise      → 企业信息
#   - StudentAuthorization → 学生授权
#   - AgentConversation → 智能体对话记忆
#
# Legacy 模型（下线计划中）：
#   - Job             → 旧岗位表，新代码请使用 JobPost
#   - TaskProgress    → 旧任务进度表，新代码请使用 GrowthTask
#   - GrowthRecord    → 旧成长记录表，保留用于历史数据查询
#
# 下线条件：前端完全迁移 + 全量测试通过 + 引用检查无残留
import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, ForeignKey, BigInteger
from sqlalchemy.orm import DeclarativeBase


def _utc_now():
    """timezone-aware UTC 时间，替代 _utc_now（消除 DeprecationWarning）。"""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


def _gen_uuid():
    """生成完整 UUID4 字符串作为主键默认值（替代旧 gen_id 的 8 字符截断）。"""
    return str(uuid.uuid4())


# 学生基本信息表
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    grade = Column(String, default="")
    major = Column(String, default="")
    target_job = Column(String, default="")
    tech_skills = Column(JSON, default=dict)
    project_exp = Column(JSON, default=list)
    soft_skills = Column(JSON, default=dict)
    domain_knowledge = Column(JSON, default=dict)
    academic_foundation = Column(JSON, default=dict)
    soft_skill_evidence = Column(JSON, default=dict)
    resume_text = Column(Text, default="")
    # --- 新档案模块化字段（Phase 1 改造） ---
    profile_sections = Column(JSON, default=dict)    # 新模块化档案结构
    profile_completeness = Column(Float, default=0.0) # 档案完整度 0-100
    phone = Column(String, default="")
    email = Column(String, default="")
    school = Column(String, default="")               # 学校（独立字段，原 major 不含学校）
    education_level = Column(String, default="")       # 学历：专科/本科/硕士/博士
    self_evaluation = Column(Text, default="")
    created_at = Column(DateTime, default=_utc_now)


# 岗位信息表
class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=_gen_uuid)
    title = Column(String, nullable=False)
    category = Column(String, default="")
    requirements = Column(JSON, default=dict)
    weight_config = Column(JSON, default=dict)
    description = Column(Text, default="")
    company = Column(String, default="")


# 诊断结果表，每个版本一条记录
class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    __table_args__ = (
        # 防止同一学生出现重复版本号（并发保护）
        # 注：SQLite ALTER TABLE 不支持事后加 UNIQUE，需在建表时声明
    )
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    version = Column(Integer, default=1)
    diagnosis_type = Column(String, default="initial")  # initial / manual_rerun / task_re_evaluation / profile_update_re_evaluation / job_target_change
    match_score = Column(Float, default=0.0)
    dimension_scores = Column(JSON, default=dict)
    dimension_changes = Column(JSON, default=dict)
    gap_details = Column(JSON, default=list)
    top5_jobs = Column(JSON, default=list)
    growth_path = Column(JSON, default=dict)
    career_advice = Column(Text, default="")
    ai_reasoning = Column(JSON, default=dict)
    # --- 阶段一/二新增字段：完整诊断数据模型 ---
    ability_profile = Column(JSON, default=dict)          # AI 生成的五维能力画像原始结果
    explanations = Column(JSON, default=dict)             # 统一解释结构（匹配分公式、维度证据、推荐理由等）
    confidence = Column(JSON, default=dict)               # 各模块置信度
    input_snapshot = Column(JSON, default=dict)           # 本次诊断使用的学生输入快照
    job_snapshot = Column(JSON, default=list)             # 本次匹配使用的岗位与权重快照
    model_name = Column(String, default="")               # 使用的 LLM 模型名称
    prompt_version = Column(String, default="")           # 提示词版本
    agent_version = Column(String, default="")            # 智能体流程版本
    ai_status = Column(String, default="available")       # available / missing_key / provider_error / schema_error / fallback_rule_based
    trigger_event = Column(String, default="")
    created_at = Column(DateTime, default=_utc_now)


# 学习任务进度表
class TaskProgress(Base):
    __tablename__ = "task_progress"
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    diagnosis_id = Column(String, ForeignKey("diagnosis_results.id"))
    phase_index = Column(Integer, default=0)
    task_index = Column(Integer, default=0)
    task_name = Column(String, default="")
    status = Column(String, default="pending")
    completed_at = Column(DateTime, nullable=True)
    evidence = Column(Text, default="")
    skill_impact = Column(JSON, default=dict)


# 成长变化历史记录表
class GrowthRecord(Base):
    __tablename__ = "growth_records"
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    record_type = Column(String, default="")
    description = Column(Text, default="")
    before_snapshot = Column(JSON, default=dict)
    after_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utc_now)


# 企业合作信息表
class Enterprise(Base):
    __tablename__ = "enterprises"
    id = Column(String, primary_key=True, default=_gen_uuid)
    name = Column(String, nullable=False)
    industry = Column(String, default="")
    description = Column(Text, default="")
    contact_name = Column(String, default="")
    contact_email = Column(String, default="")
    status = Column(String, default="active")  # pending / active / disabled
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


# 企业发布的在招岗位表
class JobPost(Base):
    __tablename__ = "job_posts"
    id = Column(String, primary_key=True, default=_gen_uuid)
    enterprise_id = Column(String, ForeignKey("enterprises.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, default="")
    description = Column(Text, default="")
    requirements_text = Column(Text, default="")
    status = Column(String, default="pending_review")  # draft / pending_review / approved / rejected / disabled
    review_reason = Column(Text, default="")
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


# 岗位能力匹配特征模型
class JobAbilityModel(Base):
    __tablename__ = "job_ability_models"
    id = Column(String, primary_key=True, default=_gen_uuid)
    job_post_id = Column(String, ForeignKey("job_posts.id"), nullable=False)
    tech_skills = Column(JSON, default=dict)
    soft_skills = Column(JSON, default=dict)
    domain_knowledge = Column(JSON, default=dict)
    project_exp = Column(JSON, default=list)
    weight_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=_utc_now)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now)


# 学生授权诊断给企业岗位记录表
class StudentAuthorization(Base):
    __tablename__ = "student_authorizations"
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    enterprise_id = Column(String, ForeignKey("enterprises.id"), nullable=False)
    job_post_id = Column(String, ForeignKey("job_posts.id"), nullable=False)
    diagnosis_id = Column(String, ForeignKey("diagnosis_results.id"), nullable=False)
    status = Column(String, default="active")  # active / revoked
    created_at = Column(DateTime, default=_utc_now)
    revoked_at = Column(DateTime, nullable=True)


# 成长任务表（阶段四：独立落库，绑定差距与预期影响）
class GrowthTask(Base):
    __tablename__ = "growth_tasks"
    id = Column(String, primary_key=True, default=_gen_uuid)
    diagnosis_id = Column(String, ForeignKey("diagnosis_results.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    phase_index = Column(Integer, default=0)
    task_index = Column(Integer, default=0)
    task_name = Column(String, default="")
    task_description = Column(Text, default="")
    linked_gap = Column(String, default="")               # 关联的能力差距维度
    target_dimension = Column(String, default="")         # 目标提升维度
    expected_impact = Column(JSON, default=dict)          # 预期影响 {"tech_skills": 0.04, ...}
    evidence_required = Column(Text, default="")          # 要求提交的证据描述
    resources = Column(JSON, default=list)                # 学习资源链接
    criteria = Column(Text, default="")                   # 达标标准
    status = Column(String, default="pending")            # pending / in_progress / completed
    submitted_evidence = Column(Text, default="")         # 学生提交的完成证据
    reviewed_by_ai = Column(JSON, default=dict)           # AI 审核结果
    re_evaluation_id = Column(String, nullable=True)      # 完成后触发的复评诊断ID
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utc_now)


# 智能体对话记忆表
class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    role = Column(String, nullable=False)  # user / assistant
    content = Column(Text, default="")
    intent = Column(String, default="")
    metadata_ = Column("metadata", JSON, default=dict)  # used_tools, question_type, next_actions
    created_at = Column(DateTime, default=_utc_now)


# 学生附件表（成绩单、外语证明等）
class StudentAttachment(Base):
    __tablename__ = "student_attachments"
    id = Column(String, primary_key=True, default=_gen_uuid)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    category = Column(String, default="other")  # transcript / language_certificate / other
    file_name = Column(String, default="")
    file_type = Column(String, default="")       # MIME type
    file_size = Column(Integer, default=0)
    storage_path = Column(String, default="")     # 相对路径
    visibility = Column(String, default="authorized_enterprises_only")
    uploaded_at = Column(DateTime, default=_utc_now)


# Agent 决策追踪表（Phase: Memory/Trace 分层）
class AgentTrace(Base):
    """记录每次 Agent 调用的决策追踪，用于可解释性、调试和前端展示。"""
    __tablename__ = "agent_traces"
    id = Column(String, primary_key=True, default=_gen_uuid)
    request_id = Column(String, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    intent = Column(String, default="")
    selected_skill = Column(String, default="")
    used_tools = Column(JSON, default=list)          # ["get_student_profile", ...]
    rejected_tools = Column(JSON, default=list)       # [{"name": "...", "reason": "..."}]
    input_summary = Column(Text, default="")          # 用户输入摘要
    output_action = Column(String, default="")        # AgentAction value
    confidence = Column(Float, default=0.0)
    limits = Column(JSON, default=list)               # 能力边界说明
    duration_ms = Column(Integer, default=0)           # 执行耗时（毫秒）
    fallback_used = Column(Integer, default=0)         # 是否使用降级 0/1
    created_at = Column(DateTime, default=_utc_now, index=True)
