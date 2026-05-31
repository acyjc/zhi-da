# 职达 — AI 人才成长智能体

> 研电赛作品 | 上传简历 → AI 解析 → 能力画像 → 岗位匹配 → 成长路径 → 持续追踪

[![技术栈](https://img.shields.io/badge/后端-FastAPI+SQLite-5b7bb5)](https://github.com/ccnnd/zhi-da)
[![技术栈](https://img.shields.io/badge/前端-React18+TypeScript-5a9e8f)](https://github.com/ccnnd/zhi-da)
[![测试](https://img.shields.io/badge/测试-pytest_14+vitest_6-6ba87a)](https://github.com/ccnnd/zhi-da)

---

## 项目简介

**职达**是一个面向大学生的 AI 职业成长智能体。不同于"一次性诊断"工具，职达强调**持续追踪**：学生上传简历 → AI 生成四维能力画像 → 匹配目标岗位 → 规划成长路径 → 标记学习任务 → 能力值自动更新 → 触发再诊断，形成完整的"诊断—学习—成长—再诊断"闭环。

### 五大核心能力

| # | 能力模块 | 说明 |
|---|---------|------|
| 1 | 学生能力画像分析 | 技术能力/项目经验/软技能/领域知识四维雷达图 |
| 2 | 岗位能力匹配分析 | 综合匹配度仪表盘 + TOP5 岗位排行 |
| 3 | 个性化学习路径规划 | AI 生成阶段目标 + 周任务 + 资源链接 + 达标标准 |
| 4 | 智能职业发展建议 | 基于差距分析的方向推荐 + AI 推理依据 |
| 5 | 精准就业指导 | 岗位推荐卡片 + 差距分析柱状图 |

---

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker（可选）

### 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/ccnnd/zhi-da.git
cd zhi-da

# 2. 启动后端
cd backend
pip install -r requirements.txt
cp .env.example .env        # 编辑 .env 填入 LLM_API_KEY
python main.py              # 默认 http://localhost:8000

# 3. 启动前端（新终端）
cd frontend
npm install
npm run dev                 # 默认 http://localhost:5173
```

### Docker 一键启动

```bash
docker-compose up --build
# 前端: http://localhost
# 后端: http://localhost:8000
```

### LLM 配置

在 `backend/.env` 中设置（不设置则使用 Mock 降级）：

```env
LLM_API_KEY=sk-xxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

---

## 项目结构

```
zhi-da/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口 & 路由注册
│   ├── config/settings.py      # 全局配置（DB/LLM/CORS/上传）
│   ├── db/
│   │   ├── database.py         # SQLite + SQLAlchemy 异步引擎
│   │   ├── models.py           # ORM 模型（Student/Job/Diagnosis/Task/Growth）
│   │   └── seed.py             # 种子数据（5 个预设岗位）
│   ├── api/routes/
│   │   ├── student.py          # 学生 CRUD
│   │   ├── job.py              # 岗位查询
│   │   ├── diagnosis.py        # SSE 流式诊断 + 历史查询
│   │   ├── progress.py         # 任务完成标记 + 技能联动更新
│   │   ├── export.py           # JSON/Excel/PDF 导出
│   │   ├── resume.py           # 简历解析（文本 + 文件上传）
│   │   ├── chat.py             # 职达小喵 LLM 对话
│   │   └── growth.py           # 成长记录查询
│   ├── core/
│   │   ├── harness/            # Pipeline 引擎
│   │   │   ├── step.py         # PipelineState + PipelineStep 基类
│   │   │   ├── runner.py       # PipelineRunner 执行器
│   │   │   ├── context.py      # ContextBuilder（Prompt 组装）
│   │   │   ├── validator.py    # SchemaValidator（JSON 校验 + 分值矫正）
│   │   │   ├── llm.py          # LLMClient 抽象层（OpenAI / Mock）
│   │   │   ├── fallback.py     # 降级策略
│   │   │   ├── tools.py        # 工具注册
│   │   │   └── logger.py       # 运行日志
│   │   ├── pipelines/          # 诊断流程
│   │   │   ├── diagnosis_pipeline.py  # 5 步初诊 Pipeline
│   │   │   └── re_evaluate_pipeline.py
│   │   ├── services/           # 业务服务
│   │   │   ├── student_service.py
│   │   │   └── job_service.py
│   │   └── models/             # Pydantic 模型
│   │       ├── student.py / job.py / diagnosis.py / progress.py
│   └── tests/                  # 测试（14 个）
│
├── frontend/                   # React + Vite 前端
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx        # 首页（左右分栏 + 几何图形）
│   │   │   ├── ProfileInput.tsx # 信息输入（简历上传→AI 解析→补全）
│   │   │   └── Dashboard.tsx   # 诊断看板（6 Tab + SSE 进度）
│   │   ├── components/
│   │   │   ├── diagnosis/      # 6 个 Tab 组件（Profile/Match/Path/Advice/Recommend/Growth）
│   │   │   ├── charts/         # ECharts 图表（Radar/Gauge/GapBar/GrowthTrend/Stage）
│   │   │   ├── shared/         # 共享组件（ProgressSteps/TaskCard/PathTimeline/ReEvaluate/AIReasoning）
│   │   │   ├── export/         # ExportToolbar（JSON/Excel/PDF）
│   │   │   └── SalaryCat/      # 桌宠小喵（纯 CSS + LLM 对话）
│   │   ├── stores/             # Zustand 状态管理
│   │   ├── services/           # API 层（axios + SSE）
│   │   ├── hooks/              # 自定义 Hook
│   │   └── types/              # TypeScript 类型定义
│   ├── index.css               # 全局主题变量
│   └── index.html
│
├── docs/                       # 文档
│   ├── superpowers/specs/      # 系统设计文档
│   ├── reports/                # 审查报告 + 工作流程报告
│   ├── user-manual.md          # 使用手册
│   └── porting-guide.md        # 移植方案
│
└── docker-compose.yml          # Docker 编排
```

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端框架 | FastAPI + uvicorn | 异步 HTTP 服务 |
| 数据库 | SQLite + SQLAlchemy (async) | 零配置嵌入式 |
| LLM 层 | OpenAI SDK（抽象接口） | 支持 Mock 降级 |
| Pipeline | 自研 Harness 引擎 | Step/Runner/Context/Validator/LLM/Fallback |
| SSE | Server-Sent Events | 流式推送诊断进度 |
| 前端框架 | React 18 + TypeScript | Vite 构建 |
| 状态管理 | Zustand | 全局状态 + localStorage 持久化 |
| 图表 | ECharts | 雷达图/仪表盘/柱状图/折线图 |
| 路由 | React Router v6 | SPA 路由 |
| 容器化 | Docker + Nginx | 生产部署 |

---

## 运行测试

```bash
# 后端（14 个测试）
cd backend
python -m pytest tests/ -v

# 前端（6 个测试）
cd frontend
npm test
```

---

## 用户流程

```
首页 → [上传简历] → [AI 解析] → [确认补全] → Dashboard
                                                      ├── 能力画像（雷达图 + 四维分值 + 技能标签云）
                                                      ├── 岗位匹配（仪表盘 + TOP5 + 差距分析）
                                                      ├── 成长路径（阶段时间线 + 任务卡片 + 标记完成）
                                                      ├── 职业建议（建议报告 + AI 推理依据）
                                                      ├── 就业推荐（5 张岗位推荐卡）
                                                      ├── 成长追踪（趋势折线图 + 版本对比 + 历史时间线）
                                                      └── 导出（JSON / Excel / PDF）
                                                               │
                                          ┌────────────────────┘
                                          │  标记任务完成 → 技能值更新 → 触发再诊断 ↓
                                          └──────────────────────────────────────────┘
```

---

## FAQ

**Q: 不配置 LLM API Key 能用吗？**
可以，系统自动使用 Mock 降级返回模拟数据，适合体验和前端调试。

**Q: 支持哪些简历格式？**
PDF、DOCX、TXT。通过 `/api/resume/upload` 上传，后端用 PyPDF2 + python-docx 提取文本后交给 LLM 解析。

**Q: 如何切换 LLM 提供商？**
修改 `backend/.env` 中的 `LLM_BASE_URL` 和 `LLM_MODEL`，兼容所有 OpenAI 接口规范的 API（DeepSeek、通义千问等）。

**Q: 数据存储在哪里？**
SQLite 数据库（`backend/db/talent_path.db`），Docker 部署时挂载到宿主机以保证持久化。

**Q: 桌宠小喵能做什么？**
点击右下角橙色猫猫展开对话面板。限制在职业成长领域（无关问题会礼貌拒绝），支持多轮上下文记忆。
