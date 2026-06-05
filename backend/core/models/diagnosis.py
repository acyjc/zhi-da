# Pydantic 模型——诊断请求/再评估请求/诊断响应
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional, Any


class DiagnoseRequest(BaseModel):
    student_id: str
    mode: str = "full"


class ReEvaluateRequest(BaseModel):
    student_id: str
    trigger_event: str = ""


class DiagnosisResponse(BaseModel):
    id: str
    student_id: str
    version: int
    diagnosis_type: str
    match_score: float
    dimension_scores: dict
    dimension_changes: dict
    gap_details: list
    top5_jobs: list
    growth_path: dict
    career_advice: str
    ai_reasoning: dict
    trigger_event: str
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

    @field_validator("ai_reasoning", "growth_path", mode="before")
    @classmethod
    def coerce_to_dict(cls, v: Any) -> dict:
        if isinstance(v, dict):
            return v
        if isinstance(v, list):
            return {"items": v}
        if v is None:
            return {}
        return {"raw": str(v)}
