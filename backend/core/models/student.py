# Pydantic 模型——学生创建/更新/响应/技能更新请求
from pydantic import BaseModel, Field
from typing import Optional


class ProjectExperience(BaseModel):
    name: str = ""
    role: str = ""
    description: str = ""
    duration: str = ""


class StudentCreate(BaseModel):
    name: str
    grade: str = ""
    major: str = ""
    target_job: str = ""
    tech_skills: dict[str, int] = Field(default_factory=dict)
    project_exp: list[ProjectExperience] = Field(default_factory=list)
    soft_skills: dict[str, int] = Field(default_factory=dict)
    domain_knowledge: dict[str, int] = Field(default_factory=dict)
    resume_text: str = Field(default="", max_length=10000)


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    target_job: Optional[str] = None
    tech_skills: Optional[dict[str, int]] = None
    project_exp: Optional[list[ProjectExperience]] = None
    soft_skills: Optional[dict[str, int]] = None
    domain_knowledge: Optional[dict[str, int]] = None
    resume_text: Optional[str] = None


class StudentResponse(BaseModel):
    id: str
    name: str
    grade: str
    major: str
    target_job: str
    tech_skills: dict[str, int]
    project_exp: list[ProjectExperience]
    soft_skills: dict[str, int]
    domain_knowledge: dict[str, int]
    resume_text: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SkillUpdateRequest(BaseModel):
    tech_skills: Optional[dict[str, int]] = None
    project_exp: Optional[list[ProjectExperience]] = None
    soft_skills: Optional[dict[str, int]] = None
    domain_knowledge: Optional[dict[str, int]] = None
