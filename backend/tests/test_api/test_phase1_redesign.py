# 阶段一改造验证测试——企业/岗位门禁、诊断版本递增、top5_jobs统一
import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import async_session, init_db
from db.models import DiagnosisResult, Enterprise, Student
from tests.conftest import auth_headers
import asyncio


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    asyncio.run(init_db())


def create_test_student(client: TestClient, name: str) -> int:
    response = client.post("/api/students", json={
        "name": name,
        "grade": "大三",
        "major": "软件工程",
        "target_job": "后端开发",
        "tech_skills": {"Python": 80},
        "soft_skills": {},
        "domain_knowledge": {},
        "project_exp": [],
        "resume_text": "test resume",
    })
    assert response.status_code == 200
    return response.json()["id"]


def create_test_diagnosis(student_id: int, version: int = 1) -> str:
    async def _create():
        async with async_session() as db:
            diag = DiagnosisResult(
                student_id=student_id,
                version=version,
                diagnosis_type="initial",
                match_score=0.75,
                dimension_scores={"tech": 0.8, "project": 0.7},
                gap_details=[],
                top5_jobs=[],
                growth_path={"phases": []},
                career_advice="test advice",
            )
            db.add(diag)
            await db.commit()
            await db.refresh(diag)
            return diag.id
    return asyncio.run(_create())


# ======== 企业状态门禁测试 ========

class TestEnterpriseStatusGate:
    """验证 pending/disabled 企业不可进入业务流"""

    def test_pending_enterprise_blocked_from_jobs(self):
        """pending 企业不能获取岗位列表"""
        with TestClient(app) as client:
            response = client.get("/api/enterprise/jobs?enterprise_id=3", headers=auth_headers("enterprise", enterprise_id="3"))
            assert response.status_code == 403
            assert "pending" in response.json()["detail"].lower() or "尚未通过审核" in response.json()["detail"]

    def test_disabled_enterprise_blocked_from_jobs(self):
        """disabled 企业不能获取岗位列表"""
        with TestClient(app) as client:
            response = client.get("/api/enterprise/jobs?enterprise_id=4", headers=auth_headers("enterprise", enterprise_id="4"))
            assert response.status_code == 403
            assert "disabled" in response.json()["detail"].lower() or "已被禁用" in response.json()["detail"]

    def test_active_enterprise_can_access_jobs(self):
        """active 企业可以正常获取岗位列表"""
        with TestClient(app) as client:
            response = client.get("/api/enterprise/jobs?enterprise_id=1", headers=auth_headers("enterprise", enterprise_id="1"))
            assert response.status_code == 200

    def test_pending_enterprise_blocked_from_create_job(self):
        """pending 企业不能创建岗位"""
        with TestClient(app) as client:
            response = client.post("/api/enterprise/jobs?enterprise_id=3", json={
                "title": "测试岗位",
                "description": "测试描述",
            }, headers=auth_headers("enterprise", enterprise_id="3"))
            assert response.status_code == 403

    def test_disabled_enterprise_blocked_from_candidates(self):
        """disabled 企业不能查看候选人"""
        with TestClient(app) as client:
            response = client.get("/api/enterprise/candidates?enterprise_id=4", headers=auth_headers("enterprise", enterprise_id="4"))
            assert response.status_code == 403

    def test_enterprise_profile_viewable_any_status(self):
        """企业资料任何状态都可查看"""
        with TestClient(app) as client:
            # pending
            r1 = client.get("/api/enterprise/profile?enterprise_id=3", headers=auth_headers("enterprise", enterprise_id="3"))
            assert r1.status_code == 200
            # disabled
            r2 = client.get("/api/enterprise/profile?enterprise_id=4", headers=auth_headers("enterprise", enterprise_id="4"))
            assert r2.status_code == 200


# ======== 学生端岗位可见性测试 ========

class TestStudentJobVisibility:
    """验证学生端只能看到 active 企业的 approved 岗位"""

    def test_student_jobs_excludes_pending_enterprise(self):
        """学生端岗位列表不包含 pending 企业的岗位"""
        with TestClient(app) as client:
            headers = auth_headers("student", student_id=9002)
            response = client.get("/api/student/jobs", headers=headers)
            assert response.status_code == 200
            jobs = response.json()
            # post_4 属于 pending 企业(id=3)，不应出现在列表中
            job_ids = [j["id"] for j in jobs]
            assert "post_4" not in job_ids

    def test_student_jobs_excludes_disabled_enterprise(self):
        """学生端岗位列表不包含 disabled 企业的岗位"""
        with TestClient(app) as client:
            response = client.get("/api/student/jobs", headers=auth_headers("student", student_id=9002))
            jobs = response.json()
            job_ids = [j["id"] for j in jobs]
            assert "post_5" not in job_ids

    def test_student_jobs_includes_active_approved(self):
        """学生端岗位列表包含 active 企业的 approved 岗位"""
        with TestClient(app) as client:
            response = client.get("/api/student/jobs", headers=auth_headers("student", student_id=9002))
            jobs = response.json()
            job_ids = [j["id"] for j in jobs]
            assert "post_1" in job_ids
            assert "post_2" in job_ids


# ======== 授权状态门禁测试 ========

class TestAuthorizationGate:
    """验证授权时检查企业状态"""

    def test_authorization_rejects_pending_enterprise_job(self):
        """不能授权给 pending 企业的岗位（即使岗位 approved）"""
        with TestClient(app) as client:
            student_id = create_test_student(client, "门禁测试学生A")
            diag_id = create_test_diagnosis(student_id)

            # post_4 属于 pending 企业(id=3)，岗位本身是 approved
            response = client.post("/api/student/authorizations", json={
                "student_id": student_id,
                "job_post_id": "post_4",
                "diagnosis_id": diag_id,
            }, headers=auth_headers("student", student_id=student_id))
            assert response.status_code == 400
            assert "not active" in response.json()["detail"].lower() or "active" in response.json()["detail"].lower()

    def test_authorization_accepts_active_enterprise(self):
        """可以正常授权 active 企业的 approved 岗位"""
        with TestClient(app) as client:
            student_id = create_test_student(client, "门禁测试学生B")
            diag_id = create_test_diagnosis(student_id)

            response = client.post("/api/student/authorizations", json={
                "student_id": student_id,
                "job_post_id": "post_1",
                "diagnosis_id": diag_id,
            }, headers=auth_headers("student", student_id=student_id))
            assert response.status_code == 200
            assert response.json()["status"] == "active"


# ======== 诊断版本递增测试 ========

class TestDiagnosisVersionIncrement:
    """验证诊断版本始终递增"""

    def test_version_always_increments(self):
        """多次诊断版本号应严格递增"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="版本测试学生",
                    grade="大三",
                    major="软件工程",
                    tech_skills={"Python": 80},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                # 创建第一个诊断
                d1 = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.7,
                )
                db.add(d1)
                await db.commit()

                # 创建第二个诊断（应该 version=2）
                from sqlalchemy import func, select
                result = await db.execute(
                    select(func.max(DiagnosisResult.version)).where(DiagnosisResult.student_id == student.id)
                )
                max_ver = result.scalar() or 0
                d2 = DiagnosisResult(
                    student_id=student.id, version=max_ver + 1,
                    diagnosis_type="manual_rerun", match_score=0.75,
                )
                db.add(d2)
                await db.commit()

                # 创建第三个诊断（应该 version=3）
                result = await db.execute(
                    select(func.max(DiagnosisResult.version)).where(DiagnosisResult.student_id == student.id)
                )
                max_ver = result.scalar() or 0
                d3 = DiagnosisResult(
                    student_id=student.id, version=max_ver + 1,
                    diagnosis_type="task_re_evaluation", match_score=0.8,
                )
                db.add(d3)
                await db.commit()

                # 验证版本号
                result = await db.execute(
                    select(DiagnosisResult).where(DiagnosisResult.student_id == student.id).order_by(DiagnosisResult.version)
                )
                diags = result.scalars().all()
                assert len(diags) == 3
                assert diags[0].version == 1
                assert diags[1].version == 2
                assert diags[2].version == 3
                assert diags[0].diagnosis_type == "initial"
                assert diags[1].diagnosis_type == "manual_rerun"
                assert diags[2].diagnosis_type == "task_re_evaluation"

        asyncio.run(_test())


# ======== top5_jobs 字段统一测试 ========

class TestTop5JobsNormalization:
    """验证 top5_jobs 字段统一使用 match_score"""

    def test_normalize_top5_jobs_from_diagnosis_route(self):
        """测试 _normalize_top5_jobs 函数"""
        from api.routes.diagnosis import _normalize_top5_jobs

        # 测试混合格式输入
        raw_jobs = [
            {"job_id": "j1", "title": "岗位A", "score": 0.85, "company": "公司A"},
            {"job_id": "j2", "title": "岗位B", "match_score": 0.72, "company": "公司B"},
            {"job_id": "j3", "title": "岗位C", "score": 1.5, "company": "公司C"},  # 超出范围
            {"job_id": "j4", "title": "岗位D", "company": "公司D"},  # 无分数
            "invalid",  # 非dict
        ]

        normalized = _normalize_top5_jobs(raw_jobs)
        assert len(normalized) == 4
        assert normalized[0]["match_score"] == 0.85
        assert normalized[1]["match_score"] == 0.72
        assert normalized[2]["match_score"] == 1.0  # 被 clamp
        assert normalized[3]["match_score"] == 0.0  # 默认值
        # 所有项都有 match_score 字段
        for job in normalized:
            assert "match_score" in job
            assert 0 <= job["match_score"] <= 1


# ======== 健康检查增强测试 ========

class TestHealthCheck:
    """验证健康检查包含 AI 状态"""

    def test_health_includes_ai_status(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
            data = response.json()
            assert "ai_status" in data
            assert "ai_available" in data
            assert "version" in data
            assert data["version"] == "2.0.0"
