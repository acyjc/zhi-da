# 导出路由——JSON 能力画像、Excel(技能+岗位)、PDF 成长路径报告
import json
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.database import get_db
from db.models import DiagnosisResult as DiagORM
from core.auth import get_current_identity, verify_student_access, Identity

router = APIRouter(prefix="/api/export", tags=["export"])


# 导出能力画像为 JSON
@router.get("/profile/{student_id}")
async def export_profile_json(
    student_id: int,
    diagnosis_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    if diagnosis_id:
        result = await db.execute(select(DiagORM).where(DiagORM.id == diagnosis_id, DiagORM.student_id == student_id))
    else:
        result = await db.execute(
            select(DiagORM).where(DiagORM.student_id == student_id).order_by(DiagORM.created_at.desc()).limit(1))
    diag = result.scalar_one_or_none()
    if not diag:
        return {"error": "No diagnosis found"}
    data = {
        "student_id": diag.student_id,
        "version": diag.version,
        "match_score": diag.match_score,
        "dimension_scores": diag.dimension_scores,
        "gap_details": diag.gap_details,
        "top5_jobs": diag.top5_jobs,
        "career_advice": diag.career_advice,
        "created_at": diag.created_at.isoformat() if diag.created_at else None,
    }
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=profile_{student_id}.json"}
    )


# 导出为 Excel(含能力画像和 TOP5 岗位两个工作表)
@router.get("/profile/{student_id}/excel")
async def export_profile_excel(
    student_id: int,
    diagnosis_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    from openpyxl import Workbook
    if diagnosis_id:
        result = await db.execute(select(DiagORM).where(DiagORM.id == diagnosis_id, DiagORM.student_id == student_id))
    else:
        result = await db.execute(
            select(DiagORM).where(DiagORM.student_id == student_id).order_by(DiagORM.created_at.desc()).limit(1))
    diag = result.scalar_one_or_none()
    if not diag:
        return {"error": "No diagnosis found"}

    wb = Workbook()
    ws = wb.active
    ws.title = "能力画像"
    ws.append(["维度", "技能", "当前值", "要求值", "差距"])

    dimension_map = {"tech": "技术能力", "project": "项目经验", "soft": "软技能", "domain": "领域知识"}
    for gap in (diag.gap_details or []):
        dim_label = dimension_map.get(gap.get("dimension", ""), gap.get("dimension", ""))
        ws.append([dim_label, gap.get("skill", ""), gap.get("current", 0), gap.get("required", 0), gap.get("gap", 0)])

    ws2 = wb.create_sheet("TOP5岗位")
    ws2.append(["排名", "岗位名称", "公司", "匹配度"])
    for i, job in enumerate(diag.top5_jobs or [], 1):
        ws2.append([i, job.get("title", ""), job.get("company", ""), f"{job.get('score', 0) * 100:.1f}%"])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=profile_{student_id}.xlsx"}
    )


# 导出成长路径规划为 PDF
@router.get("/path/{student_id}")
async def export_path_pdf(
    student_id: int,
    diagnosis_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    identity: Identity = Depends(get_current_identity),
):
    verify_student_access(student_id, identity)
    if diagnosis_id:
        result = await db.execute(select(DiagORM).where(DiagORM.id == diagnosis_id, DiagORM.student_id == student_id))
    else:
        result = await db.execute(
            select(DiagORM).where(DiagORM.student_id == student_id).order_by(DiagORM.created_at.desc()).limit(1))
    diag = result.scalar_one_or_none()
    if not diag:
        return {"error": "No diagnosis found"}

    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title_CN', parent=styles['Title'], fontSize=18, spaceAfter=12)
    heading_style = ParagraphStyle('Heading_CN', parent=styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle('Body_CN', parent=styles['Normal'], fontSize=10, leading=16)

    elements = []
    elements.append(Paragraph("TalentPath 成长路径规划报告", title_style))
    elements.append(Paragraph(f"诊断版本: V{diag.version} | 生成时间: {diag.created_at}", body_style))
    elements.append(Spacer(1, 10 * mm))

    growth_path = diag.growth_path or {}
    phases = growth_path.get("phases", [])
    for i, phase in enumerate(phases):
        elements.append(Paragraph(f"阶段 {i + 1}: {phase.get('goal', '能力提升')} ({phase.get('weeks', 4)} 周)", heading_style))
        for j, task in enumerate(phase.get("tasks", [])):
            task_text = f"<b>任务 {j + 1}: {task.get('name', '学习任务')}</b><br/>"
            task_text += f"描述: {task.get('description', '')}<br/>"
            resources = task.get("resources", [])
            if resources:
                task_text += f"资源: {', '.join(resources)}<br/>"
            task_text += f"达标标准: {task.get('criteria', '完成练习')}"
            elements.append(Paragraph(task_text, body_style))
            elements.append(Spacer(1, 3 * mm))
        elements.append(Spacer(1, 5 * mm))

    if diag.career_advice:
        elements.append(Paragraph("职业发展建议", heading_style))
        elements.append(Paragraph(diag.career_advice, body_style))

    doc.build(elements)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=growth_path_{student_id}.pdf"}
    )
