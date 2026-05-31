# Pydantic 模型——任务完成请求/进度响应
from pydantic import BaseModel, Field
from typing import Optional


class TaskCompleteRequest(BaseModel):
    student_id: str
    task_id: str
    evidence: str = Field(default="", max_length=500)


class TaskProgressResponse(BaseModel):
    id: str
    student_id: str
    diagnosis_id: Optional[str]
    phase_index: int
    task_index: int
    task_name: str
    status: str
    completed_at: Optional[str] = None
    evidence: str
    skill_impact: dict

    class Config:
        from_attributes = True
