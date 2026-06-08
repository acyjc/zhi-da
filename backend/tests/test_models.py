import pytest
from core.models.student import StudentCreate, StudentUpdate, StudentResponse, SkillUpdateRequest, ProjectExperience
from core.models.progress import TaskCompleteRequest, TaskProgressResponse
from core.models.diagnosis import DiagnoseRequest, ReEvaluateRequest


class TestStudentModels:
    def test_student_create_minimal(self):
        data = StudentCreate(name="张三")
        assert data.name == "张三"
        assert data.grade == ""
        assert data.tech_skills == {}

    def test_student_create_full(self):
        data = StudentCreate(
            name="李四",
            grade="大三",
            major="计算机科学",
            target_job="Python后端",
            tech_skills={"Python": 80, "Django": 70},
            soft_skills={"沟通表达": 60},
            domain_knowledge={"Web开发": 75},
            project_exp=[{"name": "电商平台", "role": "后端", "description": "开发API", "duration": "3个月"}],
            resume_text="个人简历内容",
        )
        assert data.tech_skills["Python"] == 80
        assert len(data.project_exp) == 1

    def test_student_update_partial(self):
        data = StudentUpdate(name="王五")
        assert data.name == "王五"
        assert data.grade is None

    def test_skill_update_request(self):
        data = SkillUpdateRequest(tech_skills={"Python": 90})
        assert data.tech_skills == {"Python": 90}
        assert data.soft_skills is None

    def test_project_experience(self):
        proj = ProjectExperience(name="项目A", role="前端", description="React开发", duration="6个月")
        assert proj.name == "项目A"
        data_dict = proj.model_dump()
        assert data_dict["role"] == "前端"


class TestDiagnosisModels:
    def test_diagnose_request(self):
        req = DiagnoseRequest(student_id=8001, mode="full")
        assert req.student_id == 8001
        assert req.mode == "full"

    def test_re_evaluate_request(self):
        req = ReEvaluateRequest(student_id=8001, trigger_event="技能更新")
        assert req.trigger_event == "技能更新"


class TestProgressModels:
    def test_task_complete_request(self):
        req = TaskCompleteRequest(student_id=8002, task_id="t1", evidence="已完成学习")
        assert req.student_id == 8002
        assert req.evidence == "已完成学习"

    def test_task_progress_response(self):
        resp = TaskProgressResponse(
            id="p1", student_id=8002, diagnosis_id="d1",
            phase_index=0, task_index=0, task_name="学Python",
            status="completed", completed_at="2024-01-01T00:00:00",
            evidence="done", skill_impact={"Python": {"delta": 10}},
        )
        assert resp.status == "completed"
        data = resp.model_dump()
        assert data["task_name"] == "学Python"
