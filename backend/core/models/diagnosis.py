# Pydantic 模型——诊断请求/再评估请求/诊断响应
from pydantic import BaseModel
from typing import Optional


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

    class Config:
        from_attributes = True
