# 数据库配置——异步 SQLAlchemy 引擎、会话工厂、建表初始化
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.settings import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def init_db():
    from db.models import Base, Enterprise, JobPost, JobAbilityModel
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed data if enterprises table is empty
    async with async_session() as session:
        from sqlalchemy import select
        res = await session.execute(select(Enterprise).limit(1))
        if res.scalar_one_or_none() is None:
            # Seed Enterprises
            ent1 = Enterprise(id='1', name='测试企业：字节跳动', industry='互联网', description='字节跳动是一家信息技术公司，致力于帮助每个人探索世界。', contact_name='HR张', contact_email='hr@bytedance.com')
            ent2 = Enterprise(id='2', name='测试企业：阿里巴巴', industry='电子商务', description='阿里巴巴集团是一家提供电子商务、云计算、数字媒体和娱乐服务的跨国科技公司。', contact_name='HR李', contact_email='hr@alibaba.com')
            session.add_all([ent1, ent2])
            
            # Seed Job Posts
            jp1 = JobPost(id='post_1', enterprise_id='1', title='Python开发工程师', category='后端开发', description='负责职达协同平台的后端核心功能开发...', requirements_text='1. 熟悉 Python, FastAPI\n2. 了解 SQLite / MySQL\n3. 熟悉 RESTful API 和 SSE 流式通信', status='approved')
            jp2 = JobPost(id='post_2', enterprise_id='1', title='前端开发工程师', category='前端开发', description='负责职达三端系统的交互重构...', requirements_text='1. 熟练掌握 React, TypeScript\n2. 熟悉 CSS 变量及暗黑模式适配\n3. 了解 ECharts 图表展示', status='approved')
            jp3 = JobPost(id='post_3', enterprise_id='2', title='AI 算法工程师', category='人工智能', description='负责职达核心大模型 Agent 架构设计...', requirements_text='1. 熟悉 PyTorch，大模型微调和 Prompt 工程\n2. 熟悉 langchain，Agent 设计模式\n3. 具备良好的数学和算法基础', status='pending_review')
            session.add_all([jp1, jp2, jp3])
            
            # Seed Job Ability Models
            am1 = JobAbilityModel(
                job_post_id='post_1',
                tech_skills={'Python': 80, 'FastAPI': 70, 'SQLite': 60},
                soft_skills={'团队协作': 70, '沟通表达': 60},
                domain_knowledge={'后端开发': 80},
                project_exp=[{'name': 'Python Web应用开发', 'description': '使用 Python 进行 Web 接口开发和持久化'}],
                weight_config={'tech_skills': 0.5, 'soft_skills': 0.2, 'domain_knowledge': 0.3}
            )
            am2 = JobAbilityModel(
                job_post_id='post_2',
                tech_skills={'React': 80, 'TypeScript': 75, 'CSS': 70},
                soft_skills={'学习能力': 80, '沟通表达': 70},
                domain_knowledge={'前端开发': 85},
                project_exp=[{'name': '前端系统构建', 'description': '使用 React 和现代工程化工具构建交互界面'}],
                weight_config={'tech_skills': 0.5, 'soft_skills': 0.2, 'domain_knowledge': 0.3}
            )
            session.add_all([am1, am2])
            
            await session.commit()
