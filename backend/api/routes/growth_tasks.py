# 成长任务路由——委托给 core/services/growth_task_service.py 处理
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from db.database import get_db
from db.models import GrowthTask, DiagnosisResult
from core.services import growth_task_service
from core.auth import require_student, verify_student_access, Identity

router = APIRouter(prefix="/api/growth-tasks", tags=["growth_tasks"])


class TaskEvidenceSubmit(BaseModel):
    student_id: int
    evidence: str


class LinkReEvaluation(BaseModel):
    re_evaluation_id: str


# 1. 获取学生的成长任务列表
@router.get("/{student_id}")
async def get_growth_tasks(
    student_id: int,
    diagnosis_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    verify_student_access(student_id, identity)
    return await growth_task_service.list_student_tasks(db, student_id, diagnosis_id)


# 2. 提交任务完成证据 + 自动执行规则审核
@router.post("/{task_id}/submit")
async def submit_task_evidence(
    task_id: str,
    req: TaskEvidenceSubmit,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    verify_student_access(req.student_id, identity)
    result = await growth_task_service.submit_evidence(db, task_id, req.student_id, req.evidence)
    if "error" in result:
        status_code = {
            "not_found": 404,
            "forbidden": 403,
            "already_completed": 400,
        }.get(result["error"], 400)
        raise HTTPException(status_code, result["message"])
    return result


# 3. 获取单个任务详情
@router.get("/{student_id}/{task_id}")
async def get_task_detail(
    student_id: int,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    verify_student_access(student_id, identity)
    result = await growth_task_service.get_task_detail(db, student_id, task_id)
    if result is None:
        raise HTTPException(404, "Growth task not found")
    return result


# 4. 复评关联——复评完成后将新诊断 ID 写回任务
@router.post("/{task_id}/link-re-evaluation")
async def link_re_evaluation(
    task_id: str,
    req: LinkReEvaluation,
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(require_student),
):
    # 校验 task 存在且属于当前学生
    task = await db.get(GrowthTask, task_id)
    if not task:
        raise HTTPException(404, "Growth task not found")
    verify_student_access(task.student_id, identity)

    # 校验 diagnosis 存在且属于当前学生
    diag = await db.get(DiagnosisResult, req.re_evaluation_id)
    if not diag:
        raise HTTPException(404, "Diagnosis result not found")
    verify_student_access(diag.student_id, identity)

    result = await growth_task_service.link_re_evaluation(db, task_id, req.re_evaluation_id)
    if "error" in result:
        raise HTTPException(404, result["message"])
    return result
