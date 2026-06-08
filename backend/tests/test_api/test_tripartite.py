import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import async_session, init_db
from db.models import DiagnosisResult
from tests.conftest import auth_headers

import asyncio

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Make sure DB schema is created for the tests
    asyncio.run(init_db())


def create_test_diagnosis(student_id: int) -> str:
    async def _create():
        async with async_session() as db:
            diag = DiagnosisResult(
                student_id=student_id,
                version=1,
                diagnosis_type="test",
                match_score=0.8,
                dimension_scores={"tech_skills": 0.8},
                gap_details=[],
                top5_jobs=[],
                growth_path={"phases": []},
                career_advice="test",
            )
            db.add(diag)
            await db.commit()
            await db.refresh(diag)
            return diag.id

    return asyncio.run(_create())


def create_test_student(client: TestClient, name: str) -> int:
    response = client.post("/api/students", json={
        "name": name,
        "grade": "大三",
        "major": "软件工程",
        "target_job": "前端开发工程师",
        "tech_skills": {"React": 80},
        "soft_skills": {},
        "domain_knowledge": {},
        "project_exp": [],
        "resume_text": "test",
    })
    assert response.status_code == 200
    return response.json()["id"]

def test_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "ai_status" in data

def test_get_student_jobs():
    with TestClient(app) as client:
        headers = auth_headers("student", student_id=9003)
        response = client.get("/api/student/jobs", headers=headers)
        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
        # Should contain seeded approved jobs
        if len(jobs) > 0:
            job = jobs[0]
            assert "id" in job
            assert "title" in job
            assert "enterprise_name" in job

def test_get_admin_summary():
    with TestClient(app) as client:
        response = client.get("/api/admin/summary", headers=auth_headers("admin", admin_account="admin"))
        assert response.status_code == 200
        summary = response.json()
        assert "total_students" in summary
        assert "total_enterprises" in summary
        assert "total_jobs" in summary
        assert "pending_jobs" in summary
        assert "active_authorizations" in summary

def test_get_admin_enterprises():
    with TestClient(app) as client:
        response = client.get("/api/admin/enterprises", headers=auth_headers("admin", admin_account="admin"))
        assert response.status_code == 200
        data = response.json()
        # API 返回分页格式 {items: [...], page, total, ...} 或列表
        ents = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(ents, list)

def test_get_admin_jobs():
    with TestClient(app) as client:
        response = client.get("/api/admin/jobs", headers=auth_headers("admin", admin_account="admin"))
        assert response.status_code == 200
        data = response.json()
        # API 返回分页格式 {items: [...], page, total, ...} 或列表
        jobs = data.get("items", data) if isinstance(data, dict) else data
        assert isinstance(jobs, list)

def test_enterprise_profile():
    with TestClient(app) as client:
        response = client.get("/api/enterprise/profile?enterprise_id=1", headers=auth_headers("enterprise", enterprise_id="1"))
        assert response.status_code == 200
        profile = response.json()
        assert profile["id"] == "1"
        assert "name" in profile


def test_authorization_rejects_diagnosis_from_other_student():
    with TestClient(app) as client:
        student_id = create_test_student(client, "授权学生A")
        other_student_id = create_test_student(client, "授权学生B")
        other_diagnosis_id = create_test_diagnosis(other_student_id)

        response = client.post("/api/student/authorizations", json={
            "student_id": student_id,
            "job_post_id": "post_2",
            "diagnosis_id": other_diagnosis_id,
        }, headers=auth_headers("student", student_id=student_id))

        assert response.status_code == 400
        assert "does not belong" in response.json()["detail"]


def test_authorization_rejects_unapproved_job():
    with TestClient(app) as client:
        student_id = create_test_student(client, "授权学生C")
        diagnosis_id = create_test_diagnosis(student_id)

        response = client.post("/api/student/authorizations", json={
            "student_id": student_id,
            "job_post_id": "post_3",
            "diagnosis_id": diagnosis_id,
        }, headers=auth_headers("student", student_id=student_id))

        assert response.status_code == 400
        assert "not approved" in response.json()["detail"]
