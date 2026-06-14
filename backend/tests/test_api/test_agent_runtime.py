# Agent 智能体测试——Planner / ContextLoader / MemoryWriter / 任务审核
import pytest
from fastapi.testclient import TestClient
from main import app
from db.database import async_session, init_db
from db.models import Student, GrowthTask, DiagnosisResult
from core.agent.runtime import ContextLoader, Planner, MemoryWriter, OutputValidator, ExplanationBuilder
from tests.conftest import auth_headers
import asyncio


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    asyncio.run(init_db())


# ======== ContextLoader 测试 ========

class TestContextLoader:
    """验证上下文加载器"""

    def test_load_existing_student(self):
        """加载已存在的学生"""
        async def _test():
            async with async_session() as db:
                # 先创建一个学生
                student = Student(
                    name="CL测试学生", grade="大三", major="软件工程",
                    target_job="后端开发", tech_skills={"Python": 80},
                    project_exp=[{"name": "项目A"}], resume_text="简历内容",
                    academic_foundation={"gpa": "3.5"},
                    soft_skill_evidence={"leadership": {"level": "中级"}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                result = await ContextLoader.load_student(db, student.id)
                assert result is not None
                assert result["name"] == "CL测试学生"
                assert result["tech_skills"]["Python"] == 80
                assert result["completeness"] if "completeness" in result else True

        asyncio.run(_test())

    def test_load_nonexistent_student(self):
        """加载不存在的学生返回 None"""
        async def _test():
            async with async_session() as db:
                result = await ContextLoader.load_student(db, 9903)
                assert result is None

        asyncio.run(_test())

    def test_check_info_completeness_full(self):
        """完整学生信息判定"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="完整学生", grade="大三", major="计算机",
                    target_job="前端开发", tech_skills={"React": 80},
                    project_exp=[{"name": "项目"}], resume_text="有简历",
                    academic_foundation={"gpa": "3.8"},
                    soft_skill_evidence={"teamwork": {"level": "高级"}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                loaded = await ContextLoader.load_student(db, student.id)
                result = await ContextLoader.check_info_completeness(loaded)
                assert result["is_complete"] is True
                assert result["completeness"] >= 0.8

        asyncio.run(_test())

    def test_check_info_completeness_missing(self):
        """信息缺失学生判定"""
        student = {
            "id": "x", "name": "残缺", "grade": "", "major": "",
            "target_job": "",
            "tech_skills": {},
            "project_exp": [],
            "resume_text": "",
            "academic_foundation": {},
            "soft_skill_evidence": {},
        }
        result = asyncio.get_event_loop().run_until_complete(
            ContextLoader.check_info_completeness(student)
        ) if False else None
        # 用同步方式测试静态方法
        async def _test():
            r = await ContextLoader.check_info_completeness(student)
            assert r["is_complete"] is False
            assert len(r["missing_fields"]) >= 3
            assert "resume_text" in r["missing_fields"]
            assert "tech_skills" in r["missing_fields"]

        asyncio.run(_test())

    def test_get_active_jobs(self):
        """获取 active 企业的 approved 岗位"""
        async def _test():
            async with async_session() as db:
                jobs = await ContextLoader.get_active_jobs(db)
                assert isinstance(jobs, list)
                # 应该包含 post_1, post_2 (active 企业 approved 岗位)
                job_ids = [j["id"] for j in jobs]
                assert "post_1" in job_ids
                assert "post_2" in job_ids
                # 不应包含 post_4 (pending企业), post_5 (disabled企业)
                assert "post_4" not in job_ids
                assert "post_5" not in job_ids

        asyncio.run(_test())


# ======== Planner 测试 ========

class TestPlanner:
    """验证规划器决策逻辑"""

    def test_planner_student_not_found(self):
        """学生不存在 -> error"""
        async def _test():
            async with async_session() as db:
                result = await Planner.plan(db, 9904)
                assert result["action"] == "error"

        asyncio.run(_test())

    def test_planner_incomplete_info(self):
        """信息不完整 -> ask_for_info"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="残缺规划学生", grade="大二",
                    # 几乎所有字段为空
                    tech_skills={}, project_exp=[],
                    resume_text="", target_job="",
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                result = await Planner.plan(db, student.id)
                assert result["action"] == "ask_for_info"
                assert "missing_fields" in result
                assert len(result["missing_fields"]) > 0

        asyncio.run(_test())

    def test_planner_no_diagnosis(self):
        """完整信息但无诊断 -> initial_diagnosis"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="无诊断规划学生", grade="大三", major="软件工程",
                    target_job="后端开发", tech_skills={"Python": 80, "Java": 70},
                    project_exp=[{"name": "项目A", "description": "desc"}],
                    resume_text="这是一份简历，包含我的个人信息和学习经历。",
                    academic_foundation={"gpa": "3.5", "rank": "前20%"},
                    soft_skill_evidence={"teamwork": {"level": "中级", "evidence": ["小组项目"]}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                result = await Planner.plan(db, student.id)
                assert result["action"] == "initial_diagnosis"

        asyncio.run(_test())

    def test_planner_with_diagnosis_no_tasks(self):
        """有诊断且无已完成任务 -> plan_or_chat"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="有诊断学生", grade="大三", major="计算机",
                    target_job="前端开发", tech_skills={"React": 80},
                    project_exp=[{"name": "项目"}],
                    resume_text="简历",
                    academic_foundation={"gpa": "3.5"},
                    soft_skill_evidence={"team": {"level": "好"}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.7,
                )
                db.add(diag)
                await db.commit()

                result = await Planner.plan(db, student.id)
                assert result["action"] == "plan_or_chat"

        asyncio.run(_test())

    def test_planner_completed_task_re_evaluation(self):
        """有已完成任务且最近诊断不是 task_re_evaluation -> re_evaluation"""
        async def _test():
            async with async_session() as db:
                student = Student(
                    name="复评学生", grade="大三", major="计算机",
                    target_job="后端开发", tech_skills={"Python": 80},
                    project_exp=[{"name": "项目"}],
                    resume_text="简历内容",
                    academic_foundation={"gpa": "3.5"},
                    soft_skill_evidence={"lead": {"level": "好"}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.7,
                )
                db.add(diag)
                await db.commit()
                await db.refresh(diag)

                # 创建已完成的成长任务
                task = GrowthTask(
                    diagnosis_id=diag.id,
                    student_id=student.id,
                    phase_index=0, task_index=0,
                    task_name="完成Python进阶",
                    status="completed",
                )
                db.add(task)
                await db.commit()

                result = await Planner.plan(db, student.id)
                assert result["action"] == "re_evaluation"
                assert result.get("trigger") == "task_completion"

        asyncio.run(_test())


# ======== MemoryWriter 测试 ========

class TestMemoryWriter:
    """验证记忆写入器"""

    def test_save_growth_tasks(self):
        """保存成长任务"""
        async def _test():
            async with async_session() as db:
                student = Student(name="MW测试学生", grade="大三", target_job="后端")
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.7,
                )
                db.add(diag)
                await db.commit()
                await db.refresh(diag)

                tasks = {
                    "phases": [
                        {
                            "tasks": [
                                {
                                    "name": "学习FastAPI",
                                    "description": "完成FastAPI官方教程",
                                    "linked_gap": "tech_skills",
                                    "target_dimension": "tech_skills",
                                    "expected_impact": {"tech_skills": 0.05},
                                    "criteria": "完成教程并提交代码",
                                    "resources": ["https://fastapi.tiangolo.com"],
                                },
                                {
                                    "name": "写项目文档",
                                    "description": "为项目编写技术文档",
                                    "linked_gap": "project_exp",
                                    "target_dimension": "project_exp",
                                    "expected_impact": {"project_exp": 0.03},
                                    "criteria": "文档覆盖核心模块",
                                    "resources": [],
                                },
                            ]
                        }
                    ]
                }

                saved = await MemoryWriter.save_growth_tasks(
                    db, student.id, diag.id, tasks
                )
                assert len(saved) == 2
                assert saved[0].task_name == "学习FastAPI"
                assert saved[0].linked_gap == "tech_skills"
                assert saved[1].task_name == "写项目文档"

        asyncio.run(_test())

    def test_save_growth_tasks_dedup(self):
        """同一诊断ID不重复保存"""
        async def _test():
            async with async_session() as db:
                student = Student(name="防重学生", grade="大三", target_job="前端")
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.6,
                )
                db.add(diag)
                await db.commit()
                await db.refresh(diag)

                tasks = {"phases": [{"tasks": [{"name": "任务A", "description": "desc"}]}]}

                # 第一次保存
                saved1 = await MemoryWriter.save_growth_tasks(db, student.id, diag.id, tasks)
                assert len(saved1) == 1

                # 第二次保存应该返回空
                saved2 = await MemoryWriter.save_growth_tasks(db, student.id, diag.id, tasks)
                assert len(saved2) == 0

        asyncio.run(_test())

    def test_save_growth_tasks_empty_phases(self):
        """空 phases 不创建任务"""
        async def _test():
            async with async_session() as db:
                student = Student(name="空阶段学生", grade="大三", target_job="数据")
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.5,
                )
                db.add(diag)
                await db.commit()
                await db.refresh(diag)

                saved = await MemoryWriter.save_growth_tasks(db, student.id, diag.id, {"phases": []})
                assert len(saved) == 0

        asyncio.run(_test())


# ======== OutputValidator 测试 ========

class TestOutputValidator:
    """验证输出校验器"""

    def test_validate_dimension_scores(self):
        scores = {"tech_skills": 0.8, "project_exp": 1.5, "academic_foundation": -0.1}
        result = OutputValidator.validate_dimension_scores(scores)
        assert result["tech_skills"] == 0.8
        assert result["project_exp"] == 1.0  # clamped
        assert result["academic_foundation"] == 0.0  # clamped
        assert result["domain_knowledge"] == 0.0  # default

    def test_validate_match_score(self):
        assert OutputValidator.validate_match_score(0.75) == 0.75
        assert OutputValidator.validate_match_score(1.5) == 1.0
        assert OutputValidator.validate_match_score(-0.3) == 0.0
        assert OutputValidator.validate_match_score("invalid") == 0.0

    def test_validate_top5_jobs(self):
        jobs = [
            {"job_id": "j1", "title": "A", "match_score": 0.9, "company": "C", "reason": "good", "matched_skills": ["Python"], "missing_skills": ["Docker"]},
            {"job_id": "j2", "title": "B", "score": 0.5, "company": "D"},
            "invalid",
        ]
        result = OutputValidator.validate_top5_jobs(jobs)
        assert len(result) == 2
        assert result[0]["reason"] == "good"
        assert result[0]["matched_skills"] == ["Python"]
        assert result[1]["match_score"] == 0.5


# ======== ExplanationBuilder 测试 ========

class TestExplanationBuilder:
    """验证解释构建器"""

    def test_build_followup_questions(self):
        questions = ExplanationBuilder.build_followup_questions(["resume_text", "target_job", "unknown_field"])
        assert len(questions) == 2  # unknown_field 不在映射中
        fields = [q["field"] for q in questions]
        assert "resume_text" in fields
        assert "target_job" in fields


# ======== Agent API 端点测试 ========

class TestAgentAPI:
    """验证 Agent API 端点"""

    def test_agent_diagnose_student_not_found(self):
        with TestClient(app) as client:
            response = client.post("/api/agent/student/9902/diagnose", headers=auth_headers("student", student_id=9902))
            assert response.status_code == 404

    def test_agent_diagnose_ask_for_info(self):
        """信息不完整的学生应该返回 ask_for_info"""
        async def _create():
            async with async_session() as db:
                student = Student(name="API残缺学生", grade="大一", tech_skills={}, project_exp=[])
                db.add(student)
                await db.commit()
                await db.refresh(student)
                return student.id

        sid = asyncio.run(_create())
        with TestClient(app) as client:
            response = client.post(f"/api/agent/student/{sid}/diagnose", headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            data = response.json()
            assert data["action"] == "ask_for_info"
            assert "followup_questions" in data

    def test_agent_plan_need_diagnosis(self):
        """无诊断历史的学生规划返回 need_diagnosis"""
        async def _create():
            async with async_session() as db:
                student = Student(name="无诊断API学生", grade="大三", target_job="后端",
                    tech_skills={"Python": 80}, project_exp=[{"name": "A"}],
                    resume_text="简历", academic_foundation={"gpa": "3.5"},
                    soft_skill_evidence={"t": {"level": "好"}})
                db.add(student)
                await db.commit()
                await db.refresh(student)
                return student.id

        sid = asyncio.run(_create())
        with TestClient(app) as client:
            response = client.post(f"/api/agent/student/{sid}/plan", headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            data = response.json()
            assert data["action"] == "need_diagnosis"

    def test_growth_tasks_empty_initially(self):
        """新学生没有成长任务"""
        async def _create():
            async with async_session() as db:
                student = Student(name="空任务学生", grade="大三")
                db.add(student)
                await db.commit()
                await db.refresh(student)
                return student.id

        sid = asyncio.run(_create())
        with TestClient(app) as client:
            response = client.get(f"/api/growth-tasks/{sid}", headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            assert response.json() == []


# ======== top5_jobs 新字段测试 ========

class TestTop5JobsNewFields:
    """验证 _normalize_top5_jobs 保留解释字段"""

    def test_normalize_preserves_reason_and_skills(self):
        from api.routes.diagnosis import _normalize_top5_jobs
        raw = [
            {
                "job_id": "j1", "title": "后端工程师", "match_score": 0.85,
                "company": "字节", "reason": "技术栈匹配度高",
                "matched_skills": ["Python", "FastAPI"],
                "missing_skills": ["Docker", "K8s"],
                "confidence": 0.9,
            },
            {
                "job_id": "j2", "title": "前端工程师", "score": 0.72,
                "company": "阿里",
                # 缺少 reason, matched_skills, missing_skills
            },
        ]
        result = _normalize_top5_jobs(raw)
        assert len(result) == 2
        # 第一个保留全部字段
        assert result[0]["reason"] == "技术栈匹配度高"
        assert result[0]["matched_skills"] == ["Python", "FastAPI"]
        assert result[0]["missing_skills"] == ["Docker", "K8s"]
        assert result[0]["confidence"] == 0.9
        # 第二个有默认值
        assert result[1]["reason"] == ""
        assert result[1]["matched_skills"] == []
        assert result[1]["missing_skills"] == []
        assert result[1]["confidence"] == 0.7  # 默认值


# ======== 复评闭环测试 ========

class TestReEvaluationLoop:
    """验证完整的 提交证据 → 自动审核 → 复评关联 闭环"""

    def _create_student_with_task(self) -> tuple[str, str, str]:
        """创建学生 + 诊断 + 成长任务，返回 (student_id, diag_id, task_id)"""
        async def _create():
            async with async_session() as db:
                student = Student(
                    name="复评闭环学生", grade="大三", major="计算机",
                    target_job="后端开发", tech_skills={"Python": 80},
                    project_exp=[{"name": "项目A"}], resume_text="简历内容",
                    academic_foundation={"gpa": "3.5"},
                    soft_skill_evidence={"lead": {"level": "好"}},
                )
                db.add(student)
                await db.commit()
                await db.refresh(student)

                diag = DiagnosisResult(
                    student_id=student.id, version=1,
                    diagnosis_type="initial", match_score=0.7,
                    growth_path={"phases": [
                        {"tasks": [
                            {"name": "学习FastAPI", "description": "完成教程",
                             "linked_gap": "tech_skills", "target_dimension": "tech_skills",
                             "expected_impact": {"tech_skills": 0.05},
                             "criteria": "完成并提交代码", "resources": []}
                        ]}
                    ]},
                )
                db.add(diag)
                await db.commit()
                await db.refresh(diag)

                from db.models import GrowthTask
                task = GrowthTask(
                    diagnosis_id=diag.id,
                    student_id=student.id,
                    phase_index=0, task_index=0,
                    task_name="学习FastAPI",
                    task_description="完成FastAPI官方教程",
                    linked_gap="tech_skills",
                    target_dimension="tech_skills",
                    expected_impact={"tech_skills": 0.05},
                    criteria="完成教程并提交代码",
                    status="pending",
                )
                db.add(task)
                await db.commit()
                await db.refresh(task)

                return student.id, diag.id, task.id

        return asyncio.run(_create())

    def test_submit_with_long_evidence_auto_approved(self):
        """提交充分证据（>50字）自动审核通过，状态变 completed"""
        sid, diag_id, task_id = self._create_student_with_task()
        evidence = "我完成了FastAPI官方教程的全部章节，包括路由、依赖注入、中间件和数据库集成。还动手实现了一个REST API项目，包含用户认证和CRUD操作，代码已推送到GitHub仓库。"

        with TestClient(app) as client:
            response = client.post(f"/api/growth-tasks/{task_id}/submit", json={
                "student_id": sid,
                "evidence": evidence,
            }, headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["review"]["preliminary_approved"] is True
            assert "审核通过" in data["review"]["feedback"]

    def test_submit_with_short_evidence_rejected(self):
        """提交不足的证据被拒绝，状态保持 in_progress"""
        sid, diag_id, task_id = self._create_student_with_task()

        with TestClient(app) as client:
            response = client.post(f"/api/growth-tasks/{task_id}/submit", json={
                "student_id": sid,
                "evidence": "做完了",
            }, headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "in_progress"
            assert data["review"]["preliminary_approved"] is False

    def test_link_re_evaluation(self):
        """复评完成后关联 re_evaluation_id"""
        sid, diag_id, task_id = self._create_student_with_task()

        # 先提交充分证据完成任务
        with TestClient(app) as client:
            client.post(f"/api/growth-tasks/{task_id}/submit", json={
                "student_id": sid,
                "evidence": "我完成了FastAPI官方教程的全部章节，包括路由、依赖注入、中间件和数据库集成。代码已推送到GitHub仓库，包含完整的测试用例和文档。",
            }, headers=auth_headers("student", student_id=sid))

        # 创建复评诊断
        async def _create_re_eval():
            async with async_session() as db:
                re_diag = DiagnosisResult(
                    student_id=sid, version=2,
                    diagnosis_type="task_re_evaluation",
                    match_score=0.75,
                )
                db.add(re_diag)
                await db.commit()
                await db.refresh(re_diag)
                return re_diag.id

        re_eval_id = asyncio.run(_create_re_eval())

        # 关联复评
        with TestClient(app) as client:
            response = client.post(f"/api/growth-tasks/{task_id}/link-re-evaluation", json={
                "re_evaluation_id": re_eval_id,
            }, headers=auth_headers("student", student_id=sid))
            assert response.status_code == 200
            data = response.json()
            assert data["re_evaluation_id"] == re_eval_id

        # 验证任务详情包含 re_evaluation_id
        with TestClient(app) as client:
            detail = client.get(f"/api/growth-tasks/{sid}/{task_id}", headers=auth_headers("student", student_id=sid))
            assert detail.status_code == 200
            assert detail.json()["re_evaluation_id"] == re_eval_id

    def test_link_re_evaluation_invalid_diagnosis(self):
        """关联不存在的诊断 ID 应返回 404"""
        sid, diag_id, task_id = self._create_student_with_task()

        with TestClient(app) as client:
            response = client.post(f"/api/growth-tasks/{task_id}/link-re-evaluation", json={
                "re_evaluation_id": "nonexistent_diag_id",
            }, headers=auth_headers("student", student_id=sid))
            assert response.status_code == 404

    def test_resubmit_after_rejection(self, monkeypatch):
        """审核未通过后允许重新提交"""
        monkeypatch.setattr("config.settings.LLM_API_KEY", "")
        sid, diag_id, task_id = self._create_student_with_task()

        with TestClient(app) as client:
            # 第一次：不充分
            r1 = client.post(f"/api/growth-tasks/{task_id}/submit", json={
                "student_id": sid,
                "evidence": "做了",
            }, headers=auth_headers("student", student_id=sid))
            assert r1.json()["status"] == "in_progress"

            # 第二次：充分
            r2 = client.post(f"/api/growth-tasks/{task_id}/submit", json={
                "student_id": sid,
                "evidence": "我详细完成了FastAPI教程中的全部章节，包括路由设计、数据验证、中间件配置和数据库操作。我还实现了一个完整的项目，包含用户注册、登录和API文档功能。",
            }, headers=auth_headers("student", student_id=sid))
            assert r2.json()["status"] == "completed"
            assert r2.json()["review"]["preliminary_approved"] is True
