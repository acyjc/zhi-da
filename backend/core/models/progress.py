# Pydantic 模型——任务完成请求/进度响应
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any


class TaskCompleteRequest(BaseModel):
    student_id: int
    task_id: str
    evidence: str = Field(default="", max_length=500)


class TaskProgressResponse(BaseModel):
    id: str
    student_id: int
    diagnosis_id: Optional[str]
    phase_index: int
    task_index: int
    task_name: str
    status: str
    completed_at: Optional[str] = None
    evidence: str
    skill_impact: dict

    model_config = {"from_attributes": True}

    @field_validator("completed_at", mode="before")
    @classmethod
    def coerce_completed_at(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v)
