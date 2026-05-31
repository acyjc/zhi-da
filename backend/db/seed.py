# 种子数据脚本——初始化 5 个岗位模板，已存在则跳过
import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'backend')

import asyncio  # noqa: E402
from sqlalchemy import select  # noqa: E402
from backend.db.database import init_db, async_session  # noqa: E402
from backend.db.models import Job  # noqa: E402

SEED_JOBS = [
    {"title": "Python后端开发工程师", "category": "技术研发", "company": "润建股份",
     "requirements": {"tech_skills": {"Python": 80, "SQL": 70, "Linux": 60, "Git": 50}, "project_exp": {"backend_projects": 65}, "soft_skills": {"teamwork": 70, "communication": 60}, "domain_knowledge": {"web_framework": 75, "database_design": 65}},
     "weight_config": {"tech": 0.4, "project": 0.2, "soft": 0.2, "domain": 0.2},
     "description": "负责后端API开发与维护，参与系统架构设计"},
    {"title": "AI算法工程师", "category": "技术研发", "company": "润建股份",
     "requirements": {"tech_skills": {"Python": 85, "机器学习": 80, "深度学习": 75, "数学": 70}, "project_exp": {"ml_projects": 75}, "soft_skills": {"逻辑思维": 80, "论文阅读": 70}, "domain_knowledge": {"CV": 70, "NLP": 70, "推荐系统": 65}},
     "weight_config": {"tech": 0.45, "project": 0.25, "soft": 0.15, "domain": 0.15},
     "description": "负责AI模型研发与优化，参与算法落地"},
    {"title": "前端开发工程师", "category": "技术研发", "company": "润建股份",
     "requirements": {"tech_skills": {"JavaScript": 80, "React": 75, "CSS": 70, "TypeScript": 65}, "project_exp": {"frontend_projects": 65}, "soft_skills": {"审美": 60, "沟通": 70}, "domain_knowledge": {"UI框架": 75, "性能优化": 60}},
     "weight_config": {"tech": 0.4, "project": 0.2, "soft": 0.2, "domain": 0.2},
     "description": "负责Web前端开发，实现高保真UI交互"},
    {"title": "数据分析师", "category": "数据", "company": "润建股份",
     "requirements": {"tech_skills": {"Python": 70, "SQL": 80, "Excel": 75, "统计学": 70}, "project_exp": {"数据分析项目": 65}, "soft_skills": {"逻辑思维": 75, "报告撰写": 70}, "domain_knowledge": {"数据可视化": 75, "业务分析": 65}},
     "weight_config": {"tech": 0.35, "project": 0.25, "soft": 0.2, "domain": 0.2},
     "description": "负责数据采集、清洗、分析与可视化报告"},
    {"title": "产品经理", "category": "产品", "company": "润建股份",
     "requirements": {"tech_skills": {"原型设计": 65, "数据分析": 60}, "project_exp": {"产品项目": 70}, "soft_skills": {"沟通协调": 85, "需求分析": 80, "项目管理": 75}, "domain_knowledge": {"行业认知": 70, "用户研究": 75}},
     "weight_config": {"tech": 0.2, "project": 0.25, "soft": 0.35, "domain": 0.2},
     "description": "负责产品规划、需求分析与项目推进"},
]


async def seed():
    await init_db()
    async with async_session() as db:
        result = await db.execute(select(Job).limit(1))
        if result.scalar_one_or_none():
            print("Seed data already exists, skipping.")
            return
        for job_data in SEED_JOBS:
            db.add(Job(**job_data))
        await db.commit()
        print(f"Seeded {len(SEED_JOBS)} jobs.")

if __name__ == "__main__":
    asyncio.run(seed())
