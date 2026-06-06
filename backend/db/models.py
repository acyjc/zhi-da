# ORM 模型定义——Student/Job/DiagnosisResult/TaskProgress/GrowthRecord 五张核心表
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# 生成短唯一 ID
def gen_id():
    return str(uuid.uuid4())[:8]


# 学生基本信息表
class Student(Base):
    __tablename__ = "students"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    grade = Column(String, default="")
    major = Column(String, default="")
    target_job = Column(String, default="")
    tech_skills = Column(JSON, default=dict)
    project_exp = Column(JSON, default=list)
    soft_skills = Column(JSON, default=dict)
    domain_knowledge = Column(JSON, default=dict)
    resume_text = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# 岗位信息表
class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=gen_id)
    title = Column(String, nullable=False)
    category = Column(String, default="")
    requirements = Column(JSON, default=dict)
    weight_config = Column(JSON, default=dict)
    description = Column(Text, default="")
    company = Column(String, default="")


# 诊断结果表，每个版本一条记录
class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    version = Column(Integer, default=1)
    diagnosis_type = Column(String, default="initial")
    match_score = Column(Float, default=0.0)
    dimension_scores = Column(JSON, default=dict)
    dimension_changes = Column(JSON, default=dict)
    gap_details = Column(JSON, default=list)
    top5_jobs = Column(JSON, default=list)
    growth_path = Column(JSON, default=dict)
    career_advice = Column(Text, default="")
    ai_reasoning = Column(JSON, default=dict)
    trigger_event = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# 学习任务进度表
class TaskProgress(Base):
    __tablename__ = "task_progress"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
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
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    record_type = Column(String, default="")
    description = Column(Text, default="")
    before_snapshot = Column(JSON, default=dict)
    after_snapshot = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


# 企业合作信息表
class Enterprise(Base):
    __tablename__ = "enterprises"
    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    industry = Column(String, default="")
    description = Column(Text, default="")
    contact_name = Column(String, default="")
    contact_email = Column(String, default="")
    status = Column(String, default="active")  # pending / active / disabled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 企业发布的在招岗位表
class JobPost(Base):
    __tablename__ = "job_posts"
    id = Column(String, primary_key=True, default=gen_id)
    enterprise_id = Column(String, ForeignKey("enterprises.id"), nullable=False)
    title = Column(String, nullable=False)
    category = Column(String, default="")
    description = Column(Text, default="")
    requirements_text = Column(Text, default="")
    status = Column(String, default="pending_review")  # draft / pending_review / approved / rejected / disabled
    review_reason = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 岗位能力匹配特征模型
class JobAbilityModel(Base):
    __tablename__ = "job_ability_models"
    id = Column(String, primary_key=True, default=gen_id)
    job_post_id = Column(String, ForeignKey("job_posts.id"), nullable=False)
    tech_skills = Column(JSON, default=dict)
    soft_skills = Column(JSON, default=dict)
    domain_knowledge = Column(JSON, default=dict)
    project_exp = Column(JSON, default=list)
    weight_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 学生授权诊断给企业岗位记录表
class StudentAuthorization(Base):
    __tablename__ = "student_authorizations"
    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"), nullable=False)
    enterprise_id = Column(String, ForeignKey("enterprises.id"), nullable=False)
    job_post_id = Column(String, ForeignKey("job_posts.id"), nullable=False)
    diagnosis_id = Column(String, ForeignKey("diagnosis_results.id"), nullable=False)
    status = Column(String, default="active")  # active / revoked
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)
