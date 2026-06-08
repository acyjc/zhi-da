# Pydantic 模型——学生创建/更新/响应/技能更新请求
# 包含新模块化档案结构（profile_sections）和附件支持
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


# ======== 旧版子模型（保持兼容） ========

class ProjectExperience(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""
    duration: str = ""


class CoreCourse(BaseModel):
    name: str
    score: float


class AcademicFoundation(BaseModel):
    gpa: str = ""
    rank: str = ""
    core_courses: list[CoreCourse] = Field(default_factory=list)
    awards: list[str] = Field(default_factory=list)
    normalized_score: int = 0


class SoftSkillDetail(BaseModel):
    level: str = "weak"
    evidence: list[str] = Field(default_factory=list)
    normalized_score: int = 40


# ======== 新模块化档案子模型 ========

class InternshipExperience(BaseModel):
    """实习经历"""
    start_date: str = ""
    end_date: str = ""
    company_name: str = ""
    position_name: str = ""
    certifier_name: str = ""
    certifier_title: str = ""
    certifier_contact: str = ""
    description: str = ""


class ProjectExperienceNew(BaseModel):
    """项目经验（新版，兼容旧 ProjectExperience）"""
    start_date: str = ""
    end_date: str = ""
    project_name: str = ""
    project_role: str = ""
    description: str = ""


class CampusExperience(BaseModel):
    """社会实践 / 校内活动"""
    start_date: str = ""
    end_date: str = ""
    activity_name: str = ""
    role: str = ""
    description: str = ""


class Award(BaseModel):
    """奖励荣誉"""
    award_date: str = ""
    award_name: str = ""
    level: str = ""           # 国家级 / 省级 / 校级
    description: str = ""


class SkillItem(BaseModel):
    """技能 / 爱好"""
    name: str = ""
    level: str = ""           # 入门 / 了解 / 熟练 / 精通
    description: str = ""


class Publication(BaseModel):
    """论文 / 专利"""
    pub_type: str = ""        # 论文 / 专利
    name: str = ""
    pub_date: str = ""
    description: str = ""


class JobIntention(BaseModel):
    """求职意向"""
    target_job: str = ""
    expected_industry: str = ""
    job_type: str = ""        # 实习 / 校招 / 全职
    available_date: str = ""


class EducationInfo(BaseModel):
    """教育经历（与基本信息部分字段互补）"""
    school: str = ""
    education_level: str = ""  # 专科 / 本科 / 硕士 / 博士
    major: str = ""
    rank_description: str = "" # 专业排名 / 成绩说明
    english_level: str = ""    # CET-4 / CET-6 / IELTS / TOEFL 等


class ProfileSections(BaseModel):
    """新模块化档案结构"""
    basic_info: dict = Field(default_factory=dict)
    education: Optional[EducationInfo] = None
    job_intention: Optional[JobIntention] = None
    internship_exp: list[InternshipExperience] = Field(default_factory=list)
    project_exp: list[ProjectExperienceNew] = Field(default_factory=list)
    campus_exp: list[CampusExperience] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    skills: list[SkillItem] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    self_evaluation: str = ""


# ======== 附件模型 ========

class AttachmentMeta(BaseModel):
    """附件元信息"""
    id: str = ""
    category: str = "other"    # transcript / language_certificate / other
    file_name: str = ""
    file_type: str = ""
    file_size: int = 0
    uploaded_at: str = ""
    visibility: str = "authorized_enterprises_only"


# ======== 请求/响应模型 ========

class StudentCreate(BaseModel):
    name: str
    grade: str = ""
    major: str = ""
    target_job: str = ""
    # 旧字段保持兼容
    tech_skills: dict[str, int] = Field(default_factory=dict)
    project_exp: list[ProjectExperience] = Field(default_factory=list)
    soft_skills: dict[str, int] = Field(default_factory=dict)
    domain_knowledge: dict[str, int] = Field(default_factory=dict)
    resume_text: str = Field(default="", max_length=10000)
    academic_foundation: Optional[AcademicFoundation] = None
    soft_skill_evidence: Optional[dict[str, SoftSkillDetail]] = None
    # 新字段
    school: str = ""
    education_level: str = ""
    phone: str = ""
    email: str = ""
    self_evaluation: str = ""
    profile_sections: Optional[ProfileSections] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    target_job: Optional[str] = None
    # 旧字段保持兼容
    tech_skills: Optional[dict[str, int]] = None
    project_exp: Optional[list[ProjectExperience]] = None
    soft_skills: Optional[dict[str, int]] = None
    domain_knowledge: Optional[dict[str, int]] = None
    resume_text: Optional[str] = None
    academic_foundation: Optional[AcademicFoundation] = None
    soft_skill_evidence: Optional[dict[str, SoftSkillDetail]] = None
    # 新字段
    school: Optional[str] = None
    education_level: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    self_evaluation: Optional[str] = None
    profile_sections: Optional[ProfileSections] = None


class StudentResponse(BaseModel):
    id: int
    name: str
    grade: str
    major: str
    target_job: str
    # 旧字段保持兼容
    tech_skills: dict[str, int]
    project_exp: list[ProjectExperience]
    soft_skills: dict[str, int]
    domain_knowledge: dict[str, int]
    resume_text: str
    academic_foundation: Optional[AcademicFoundation] = None
    soft_skill_evidence: Optional[dict[str, SoftSkillDetail]] = None
    # 新字段
    school: str = ""
    education_level: str = ""
    phone: str = ""
    email: str = ""
    self_evaluation: str = ""
    profile_sections: Optional[dict] = None
    profile_completeness: float = 0.0
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("created_at", mode="before")
    @classmethod
    def coerce_created_at(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)

    @field_validator("profile_sections", mode="before")
    @classmethod
    def coerce_profile_sections(cls, v: Any) -> Optional[dict]:
        if v is None:
            return None
        if isinstance(v, dict):
            return v
        if hasattr(v, "model_dump"):
            return v.model_dump()
        return v


class SkillUpdateRequest(BaseModel):
    tech_skills: Optional[dict[str, int]] = None
    project_exp: Optional[list[ProjectExperience]] = None
    soft_skills: Optional[dict[str, int]] = None
    domain_knowledge: Optional[dict[str, int]] = None
    academic_foundation: Optional[AcademicFoundation] = None
    soft_skill_evidence: Optional[dict[str, SoftSkillDetail]] = None
