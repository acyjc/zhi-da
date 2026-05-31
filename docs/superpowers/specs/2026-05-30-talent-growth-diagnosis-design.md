# 方向一：学生成长诊断与路径规划 — 系统设计文档

> **项目名称**：TalentPath — AI驱动的人才培养与精准就业智能体
> **日期**：2026-05-30
> **版本**：v3.1（架构审查修订：轻量Harness + 安全章节）

---

## 一、系统概述

### 1.1 产品定位

**用户向智能体**——面向学生个体的 AI 职业成长伙伴。不仅是"一次性诊断"，更是**持续追踪**的成长管家。学生通过提交简历或填写个人信息，获得能力画像、岗位匹配、成长路径和职业建议，在学习过程中系统持续追踪成长进度，**四维诊断结果随能力变化动态刷新**，形成"诊断 → 学习 → 成长 → 再诊断"的完整闭环。

### 1.2 用户流程（动态闭环）

```
 ┌──────────┐     ┌──────────────┐     ┌──────────────────────────────────┐
 │  首页     │ ──► │  信息输入     │ ──► │  一站式诊断看板                     │
 │  Welcome  │     │  简历上传     │     │  [画像][匹配][路径][建议][推荐]      │
 └──────────┘     └──────────────┘     │            + 导出                  │
                                        └──────────────┬───────────────────┘
                                                       │
                                          ┌────────────▼───────────────────┐
                                          │         动态成长闭环             │
                                          │                                │
                                          │  标记任务完成 ──► 能力值更新      │
                                          │       ▲              │         │
                                          │       │              ▼         │
                                          │       └──── 触发再诊断 ◄──┘     │
                                          │  (匹配/路径/建议/推荐全部刷新)     │
                                          └────────────────────────────────┘
```

**核心设计原则**：系统不是给一次答案就结束，而是像一个真正的导师一样，在学生成长的每个阶段都能给出适配的建议。

### 1.3 五大核心能力（方向一）

| # | 能力模块 | 说明 |
|---|---------|------|
| 1 | 学生能力画像分析 | 四维能力量化模型，生成学生能力雷达图 |
| 2 | 岗位能力匹配分析 | 双向匹配算法，量化学生-岗位差距 |
| 3 | 个性化学习路径规划 | AI生成阶段目标+周任务+资源链接+达标标准 |
| 4 | 智能职业发展建议 | 基于差距分析的职业方向推荐 |
| 5 | 精准就业指导与推荐 | TOP5岗位匹配+理由+行动建议 |

### 1.4 差异化创新点

| # | 创新关键词 | 说明 |
|---|-----------|------|
| 1 | **多维度能力量化模型** | 自建四维能力评估体系（技术/项目/软技能/领域），超越简单关键词匹配 |
| 2 | **可解释AI路径规划** | 每条成长建议标注推理依据和置信度，AI决策过程透明可审计 |
| 3 | **Harness Engineering架构** | LLM负责理解生成，Harness负责上下文管理、工具调用、执行编排、状态管理、输出校验、日志观测、失败恢复 |
| 4 | **动态成长闭环** | 学生标记任务完成 → 能力值自动更新 → 触发全维度再诊断（匹配/路径/建议/推荐全部刷新），形成持续追踪的反馈循环 |
| 5 | **结构化输出约束** | JSON Schema强制校验，确保AI输出格式稳定可靠 |

### 1.5 动态成长闭环机制

#### 1.5.1 闭环触发条件

学生的能力值发生变化时，系统自动触发对应维度的再诊断：

| 触发事件 | 影响维度 | 刷新范围 |
|---------|---------|---------|
| 完成学习任务（标记 ✓） | 能力画像 → 全部四维 | 匹配度 / 路径 / 建议 / 推荐 |
| 新增项目经验 | 项目经验维度 | 匹配度 / 建议 / 推荐 |
| 更新技能水平 | 技术能力维度 | 匹配度 / 路径 / 推荐 |
| 完成阶段性考核 | 全维度 | 全部刷新 |
| 手动触发「重新诊断」 | 全维度 | 全部刷新 |

#### 1.5.2 动态变化可视化

诊断看板不只是展示"当前结果"，更展示 **"从上次到现在的变化"**：

```
┌─────────────────────────────────────────────────────┐
│ 能力画像                     上次诊断: 2026-05-15    │
│                                                      │
│  技术能力: 65 → 72  ▲+7    项目经验: 60 → 60  —     │
│  软技能:   75 → 78  ▲+3    领域知识: 50 → 58  ▲+8   │
│                                                      │
│  岗位匹配度: 62% → 71%  ▲+9                         │
│    ▸ TOP1 岗位从「后端初级」→「后端中级」              │
│                                                      │
│  成长路径: 阶段2/3 进行中 ▸ 2周后进入阶段3            │
└─────────────────────────────────────────────────────┘
```

#### 1.5.3 诊断历史链

每次诊断结果形成一条带时间戳的记录，前端以时间线展示：
- 初诊（Day 0）：基准画像 + 初始匹配 + 第一阶段路径
- 再诊（Day 14）：能力变化 + 匹配刷新 + 路径推进
- 再诊（Day 30）：...

每条历史记录包含完整的诊断快照，支持导出和对比。

---

## 二、Harness Engineering 架构设计

### 2.1 技术路线决策

经架构审查，采用 **"LangGraph 思想 + 自研轻量 Harness"** 路线：

| 方案 | 决策 | 理由 |
|------|------|------|
| 全量 LangGraph | ❌ 不采用 | 本项目是确定性诊断 Pipeline，非开放式复杂 Agent |
| 完全自研复杂 Harness | ❌ 不采用 | 开发周期长、质量风险高 |
| **轻量 Harness（吸收 LangGraph 思想）** | ✅ 采用 | 6 个模块的最小可用实现，吸收 State/Node/Edge 思想 |
| 后期可插拔 LangGraph | ✅ 保留 | 通过抽象接口预留替换口 |

### 2.2 V1 最小 Harness 定义

V1 只做六个模块，不做复杂状态图、多 Agent 通信、自动规划、反思循环：

```
harness/
├── runner.py      # PipelineRunner — 状态驱动执行器（吸收 LangGraph State 思想）
├── step.py        # PipelineStep — 步骤基类（吸收 LangGraph Node 思想）
├── context.py     # ContextBuilder — 上下文组装器
├── validator.py   # SchemaValidator — 输出校验器
├── logger.py      # RunLogger — 执行观测器
└── fallback.py    # FallbackHandler — 容错处理器
```

```
┌─────────────────────────────────────────────────────┐
│              PipelineRunner                          │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐           │
│  │  Step 1 │──►│  Step 2 │──►│  Step 3 │──► ...    │
│  │  画像    │   │  匹配    │   │  路径    │           │
│  └─────────┘   └─────────┘   └─────────┘           │
│       ▲                            │               │
│       │         State              │               │
│       └────────────────────────────┘               │
│  ┌─────────────────────────────────────────────┐   │
│  │ ContextBuilder │ SchemaValidator │ RunLogger │   │
│  │ FallbackHandler│   ToolRegistry              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 2.3 六大模块职责

#### PipelineRunner（状态驱动执行器）

- 吸收 LangGraph 的 State 思想：维护 `PipelineState`，在步骤间传递
- 按顺序执行 `PipelineStep` 列表
- 步骤失败时调用 FallbackHandler
- 预留 `async def run(self, input) -> PipelineState` 抽象接口，后续可替换为 LangGraph

#### PipelineStep（步骤基类）

- 每个诊断阶段对应一个 Step（`ProfileStep`, `MatchStep`, `PathStep`, `AdviceStep`）
- 统一接口：`async def execute(self, state: PipelineState) -> PipelineState`
- 步骤通过 `state` 对象共享中间结果，吸收 LangGraph 的 Edge 思想

#### ContextBuilder

- 根据当前 PipelineState 组装 LLM System Prompt + User Message
- 注入领域约束（禁止回答超出人才培养范围的问题→防御 Prompt 注入）
- 后期扩展 RAG 能力

#### SchemaValidator

- 对每个 Step 的 LLM 输出做 JSON Schema 校验
- 数值范围检查（匹配度 [0,1]、分值 [0,100]）
- 格式不合法时触发自动修复（重试 LLM 调用）

#### RunLogger（执行观测器）

- 记录每次 LLM 调用：输入/输出/耗时/Token 消耗
- 记录 Pipeline 执行轨迹：步骤顺序/状态变化/错误
- 结构化日志输出

#### FallbackHandler（容错处理器）

- LLM 调用失败：指数退避重试（最多 3 次）
- 连续失败：降级为规则引擎兜底
- 部分步骤失败：返回已完成结果 + 失败标记

### 2.4 Pipeline 定义（诊断流程）

```python
# pipelines/diagnosis_pipeline.py
diagnosis_pipeline = [
    ProfileStep(name="profile"),
    MatchStep(name="match", depends_on=["profile"]),
    GapStep(name="gap", depends_on=["match"]),
    PathStep(name="path", depends_on=["gap"]),
    AdviceStep(name="advice", depends_on=["path"]),
]
```

### 2.5 LLM 抽象层

```python
# harness/llm.py
class LLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list, tools: list = None) -> LLMResponse: ...
    @abstractmethod
    async def stream(self, messages: list, tools: list = None) -> AsyncIterator[LLMChunk]: ...

class OpenAIClient(LLMClient): ...    # OpenAI 实现
class LocalClient(LLMClient): ...     # 本地模型实现（后续扩展）
```

所有 Agent 通过 `LLMClient` 抽象接口调用 LLM，切换模型无需修改业务代码。

---

## 三、技术栈

### 3.1 后端

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 框架 | Python FastAPI | 异步高性能、自动 API 文档、类型安全 |
| LLM SDK | OpenAI SDK + LangChain | 灵活切换模型，支持 Function Calling |
| 数据库 | SQLite + SQLAlchemy | 零配置、轻量级、适合演示 |
| 数据校验 | Pydantic v2 | 与 FastAPI 深度集成，JSON Schema 支持 |
| 异步任务 | asyncio | 支持并行 LLM 调用 |
| PDF 生成 | ReportLab / WeasyPrint | 路径规划报告输出 |
| Excel 导出 | openpyxl | 能力画像导出 |

### 3.2 前端

| 组件 | 技术选型 | 理由 |
|------|---------|------|
| 框架 | React 18 + TypeScript | 生态丰富、类型安全 |
| 构建工具 | Vite | 极速 HMR |
| UI 组件库 | Ant Design 5 | 成熟的企业级组件库 |
| 图表 | ECharts + echarts-for-react | 雷达图、柱状图、热力图 |
| 状态管理 | Zustand | 轻量级、API 简洁 |
| HTTP 客户端 | axios | 拦截器支持、错误处理 |
| 路由 | React Router v6 | SPA 路由 |

### 3.3 部署

| 组件 | 技术选型 |
|------|---------|
| 容器化 | Docker + docker-compose |
| 前端服务 | Nginx 静态文件 |
| 后端服务 | uvicorn + gunicorn |

---

## 四、系统架构

### 4.1 整体架构图

```
┌──────────────────────────────────────────────────────────┐
│                        用户（学生）                         │
│              提交简历 / 填写信息 / 选择目标岗位               │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────┐     HTTP/SSE     ┌──────────────┐     API Call     ┌──────────────┐
│   React SPA  │ ◄──────────────► │   FastAPI    │ ◄──────────────► │   LLM API    │
│  3页流程:     │                  │   (uvicorn)  │                  │ (OpenAI等)   │
│  首页→输入   │                  │              │                  │              │
│  →看板       │                  │  ┌─────────┐ │                  └──────────────┘
└──────────────┘                  │  │ Harness  │ │
                                  │  │ Engine   │ │
                                  │  └────┬────┘ │
                                  └───────┼──────┘
                                          │
                                    ┌─────┴─────┐
                                    │  SQLite   │
                                    └───────────┘
```

### 4.2 前端路由设计

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | Home | 产品介绍 + "开始诊断" CTA |
| `/input` | ProfileInput | 信息输入（简历上传/手动填写） |
| `/dashboard` | Dashboard | 一站式诊断看板（需完成输入后进入） |

> **设计意图**：3 个页面即可覆盖完整用户流程。看板内部用 Tab 切换展示不同诊断结果，无需多页面跳转。

```
### 4.3 后端分层设计

```
api/                  # 路由层 - HTTP 接口定义
├── routes/
│   ├── student.py    # 学生管理 API
│   ├── job.py        # 岗位管理 API
│   ├── diagnosis.py  # 诊断分析 API（核心）
│   ├── progress.py   # 任务进度 API
│   └── export.py     # 导出 API

core/                 # 核心逻辑层
├── harness/          # Harness Engineering 模块（V1 轻量）
│   ├── runner.py          # PipelineRunner — 状态驱动执行器
│   ├── step.py            # PipelineStep — 步骤基类
│   ├── context.py         # ContextBuilder — 上下文组装器
│   ├── validator.py       # SchemaValidator — 输出校验器
│   ├── logger.py          # RunLogger — 执行观测器
│   ├── fallback.py        # FallbackHandler — 容错处理器
│   ├── llm.py             # LLMClient — LLM抽象层
│   └── tools.py           # ToolRegistry — 工具注册中心
├── pipelines/        # 流程定义
│   ├── diagnosis_pipeline.py    # 初诊流程
│   └── re_evaluate_pipeline.py  # 再诊流程
├── agents/           # PipelineStep 实现
│   ├── profile_step.py       # 能力画像 Step
│   ├── match_step.py         # 岗位匹配 Step
│   ├── gap_step.py           # 差距分析 Step
│   ├── path_step.py          # 路径规划 Step
│   └── advice_step.py        # 职业建议 Step
├── models/           # Pydantic 数据模型
│   ├── student.py
│   ├── job.py
│   ├── diagnosis.py
│   └── progress.py
└── services/         # 业务服务层
    ├── student_service.py
    ├── job_service.py
    ├── diagnosis_service.py
    ├── progress_service.py
    └── export_service.py

db/                   # 数据层
├── database.py       # SQLAlchemy 配置
├── models.py         # ORM 模型
└── seed.py           # 种子数据

config/               # 配置
└── settings.py

tests/                # 测试
├── test_harness/
├── test_agents/
└── test_api/
```

### 4.3 前端组件树（用户向设计）

```
src/
├── pages/
│   ├── Home.tsx               # 首页 - Welcome + 开始诊断 CTA
│   ├── ProfileInput.tsx       # 信息输入页（核心）- 简历上传 + 手动补全
│   └── Dashboard.tsx          # 一站式诊断看板（核心）- 多Tab结果展示
├── components/
│   ├── diagnosis/
│   │   ├── ProfileTab.tsx     # 能力画像Tab - 雷达图 + 四维分值 + 变化差
│   │   ├── MatchTab.tsx       # 岗位匹配Tab - 仪表盘 + 差距表 + TOP5排名
│   │   ├── PathTab.tsx        # 成长路径Tab - 时间线 + 任务卡片(可标记完成)
│   │   ├── AdviceTab.tsx      # 职业建议Tab - 推荐理由 + AI推理
│   │   ├── RecommendTab.tsx   # 就业推荐Tab - 岗位列表
│   │   └── GrowthTab.tsx      # 成长追踪Tab - 诊断历史 + 版本对比 + 变化曲线
│   ├── charts/
│   │   ├── RadarChart.tsx     # 能力雷达图（支持多版本叠加对比）
│   │   ├── MatchGauge.tsx     # 匹配度仪表盘（标注变化趋势）
│   │   ├── GapBar.tsx         # 差距柱状图
│   │   ├── GrowthTrend.tsx    # 能力变化折线图（时间轴）
│   │   └── AbilityHeatmap.tsx # 能力热力图
│   ├── shared/
│   │   ├── PathTimeline.tsx   # 路径时间线
│   │   ├── TaskCard.tsx       # 任务卡片（含完成标记）
│   │   ├── SkillTagCloud.tsx  # 技能标签云
│   │   ├── ProgressSteps.tsx  # 步骤进度条
│   │   ├── AIReasoning.tsx    # AI推理依据展示
│   │   └── ReEvaluatePrompt.tsx # 再诊断提示弹窗
│   └── export/
│       └── ExportToolbar.tsx  # 导出工具栏
├── hooks/
│   ├── useDiagnosis.ts        # 诊断流程 Hook（SSE流式）
│   ├── useReEvaluate.ts       # 再诊断 Hook
│   ├── useProgress.ts         # 任务进度 Hook
│   └── useExport.ts           # 导出 Hook
├── stores/
│   └── appStore.ts            # 全局状态（当前用户、诊断结果）
├── services/
│   └── api.ts                 # API 调用封装
└── types/
    └── index.ts               # TypeScript 类型定义
```

---

## 五、数据模型设计

### 5.1 核心实体

#### 学生 (Student)

```python
class Student:
    id: str
    name: str
    grade: str              # 年级
    major: str              # 专业
    target_job: str         # 目标岗位
    tech_skills: JSON       # 技术能力 {Python: 80, SQL: 65, ...}
    project_exp: JSON       # 项目经验 [{name, role, desc, duration}]
    soft_skills: JSON       # 软技能 {communication: 75, teamwork: 80, ...}
    domain_knowledge: JSON  # 领域知识 {AI: 70, backend: 60, ...}
    resume_text: str        # 简历原文
```

#### 岗位 (Job)

```python
class Job:
    id: str
    title: str              # 岗位名称
    category: str           # 岗位类别
    requirements: JSON      # 能力要求 {tech_skills: {}, soft_skills: {}, domain: {}}
    weight_config: JSON     # 各维度权重 {tech: 0.4, project: 0.2, soft: 0.2, domain: 0.2}
    description: str        # 岗位描述
    company: str            # 企业名称
```

#### 诊断结果 (DiagnosisResult)

```python
class DiagnosisResult:
    id: str
    student_id: str
    version: int            # 诊断版本号（1=初诊, 2=第一次再诊...）
    diagnosis_type: str     # "initial" | "re_evaluation" | "manual"
    match_score: float      # 综合匹配度 [0,1]
    dimension_scores: JSON  # 四维分值 {tech: 0.75, project: 0.60, soft: 0.85, domain: 0.50}
    dimension_changes: JSON # 相对上次变化 {tech: +0.07, project: 0, soft: +0.03, domain: +0.08}
    gap_details: JSON       # 差距明细 [{dimension, skill, current, required, gap, trend}]
    top5_jobs: JSON         # TOP5匹配岗位（含排名变化标注）
    growth_path: JSON       # 成长路径 {phases: [{goal, weeks, tasks, resources, criteria}]}
    career_advice: str      # 职业建议
    ai_reasoning: JSON      # AI推理依据（可解释性，含"为何变化"的解释）
    trigger_event: str      # 触发事件描述 "完成3个学习任务" / "手动重诊"
    created_at: datetime
```

#### 任务进度 (TaskProgress)

```python
class TaskProgress:
    id: str
    student_id: str
    diagnosis_id: str       # 关联的某次诊断中的路径任务
    phase_index: int        # 阶段序号
    task_index: int         # 任务序号
    task_name: str          # 任务名称
    status: str             # "pending" | "in_progress" | "completed"
    completed_at: datetime  # 完成时间
    evidence: str           # 完成凭证（描述/链接）
    skill_impact: JSON      # 对能力值的影响预估 {skill: "Python", delta: +5}
```

#### 成长记录 (GrowthRecord)

```python
class GrowthRecord:
    id: str
    student_id: str
    record_type: str        # "skill_change" | "project_added" | "task_completed" | "re_diagnosis"
    description: str        # 事件描述
    before_snapshot: JSON   # 变化前的关键数据快照
    after_snapshot: JSON    # 变化后的关键数据快照
    created_at: datetime
```

### 5.2 四维能力量化模型

```
能力画像 = {
  "技术能力": {
    "weight": 0.35,
    "sub_items": [
      {"name": "编程语言", "score": 78, "level": "熟练"},
      {"name": "框架工具", "score": 65, "level": "了解"},
      ...
    ]
  },
  "项目经验": {
    "weight": 0.25,
    "sub_items": [
      {"name": "项目复杂度", "score": 60, "level": "中等"},
      {"name": "角色贡献度", "score": 70, "level": "核心成员"},
      ...
    ]
  },
  "软技能": {
    "weight": 0.20,
    "sub_items": [
      {"name": "沟通表达", "score": 75, "level": "良好"},
      {"name": "团队协作", "score": 80, "level": "优秀"},
      ...
    ]
  },
  "领域知识": {
    "weight": 0.20,
    "sub_items": [
      {"name": "AI/ML", "score": 72, "level": "熟悉"},
      {"name": "后端开发", "score": 60, "level": "了解"},
      ...
    ]
  }
}
```

---

## 六、API 设计

### 6.1 核心 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/students` | 创建学生（初始化） |
| `GET` | `/api/students/{id}` | 获取学生详情 |
| `GET` | `/api/jobs` | 获取岗位列表 |
| `POST` | `/api/diagnosis/full` | **初诊**：全流程诊断（一键） |
| `POST` | `/api/diagnosis/re-evaluate` | **再诊**：基于最新能力值重新诊断 |
| `GET` | `/api/diagnosis/history/{student_id}` | 获取诊断历史链 |
| `GET` | `/api/diagnosis/{id}` | 获取某次诊断详情 |
| `POST` | `/api/progress/task-complete` | 标记任务完成 → 更新能力值 |
| `PATCH` | `/api/progress/task/{id}` | 更新任务状态 |
| `GET` | `/api/progress/{student_id}` | 获取当前任务进度 |
| `PUT` | `/api/students/{id}/skills` | 手动更新技能水平 |
| `GET` | `/api/growth/records/{student_id}` | 获取成长记录时间线 |
| `GET` | `/api/export/profile/{student_id}` | 导出能力画像 JSON/Excel |
| `GET` | `/api/export/path/{student_id}` | 导出路径规划 PDF |

### 6.2 关键接口定义

#### 全流程诊断接口

```
POST /api/diagnosis/full
Request:
{
  "student_id": "stu_001",
  "mode": "full"  # full | profile_only | match_only
}

Response (SSE 流式):
event: progress
data: {"stage": "profile", "progress": 0.2, "message": "正在生成能力画像..."}

event: progress
data: {"stage": "match", "progress": 0.4, "message": "正在进行岗位匹配分析..."}

event: result
data: {
  "diagnosis_id": "diag_v3_001",
  "version": 1,
  "diagnosis_type": "initial",
  "profile": { ... },
  "match_result": { ... },
  "gap_analysis": { ... },
  "growth_path": { ... },
  "career_advice": { ... },
  "ai_reasoning": { ... }
}
```

#### 再诊断接口（动态闭环核心）

```
POST /api/diagnosis/re-evaluate
Request:
{
  "student_id": "stu_001",
  "trigger_event": "完成3个学习任务"  # 自动触发时的描述
}

Response (SSE 流式):
event: progress
data: {"stage": "detecting_changes", "progress": 0.1, "message": "检测到能力变化：技术能力+7, 领域知识+8..."}

event: progress
data: {"stage": "re_match", "progress": 0.3, "message": "重新计算岗位匹配度..."}

event: progress
data: {"stage": "re_path", "progress": 0.5, "message": "更新成长路径..."}

event: progress
data: {"stage": "re_advice", "progress": 0.7, "message": "刷新职业建议..."}

event: result
data: {
  "diagnosis_id": "diag_v3_002",
  "version": 2,
  "previous_version": 1,
  "dimension_changes": { "tech": +0.07, "project": 0, "soft": +0.03, "domain": +0.08 },
  "match_score_change": +0.09,
  "top_job_changed": true,
  "path_phase_advanced": "阶段2/3 → 阶段3/3",
  ... (完整的诊断结果)
}
```

#### 任务完成接口（触发动态更新）

```
POST /api/progress/task-complete
Request:
{
  "student_id": "stu_001",
  "task_id": "task_phase1_3",
  "evidence": "完成LeetCode 50题，通过率85%"
}

Response:
{
  "success": true,
  "skill_updates": {
    "Python": { "before": 65, "after": 72, "delta": +7 },
    "算法": { "before": 60, "after": 68, "delta": +8 }
  },
  "should_re_evaluate": true,  # 前端据此提示用户是否要重新诊断
  "diagnosis_suggested": "你的技术能力有显著提升，建议重新诊断以获得更精准的岗位匹配和路径规划"
}
```

---

## 七、安全设计

> 架构审查发现安全层面完全空白，本章为 v3.1 新增补充。

### 7.1 认证策略（演示版）

比赛演示环境（本地 Docker）采用最小可行方案：

| 层级 | 措施 | 说明 |
|------|------|------|
| 学生身份 | Session 模拟 | 前端 localStorage 存储 `student_id`，后端仅校验该 ID 存在 |
| API 访问 | 无认证 | 演示环境不设认证墙，评审可直接操作 |
| 生产扩展 | JWT Token | 代码注入点保留，未来可快速切换到 JWT 认证 |

> **设计说明**：这是比赛演示的刻意简化，非设计缺陷。代码中预留 `Depends(get_current_user)` 依赖注入点。

### 7.2 输入安全

| 防护点 | 措施 | 实现位置 |
|--------|------|---------|
| 简历上传 | 文件类型白名单：`.pdf`, `.docx`, `.txt`；大小限制 10MB | `api/routes/student.py` |
| 自由文本输入 | 长度截断：resume_text ≤ 10000字，evidence ≤ 500字 | Pydantic Model `max_length` |
| LLM Prompt 注入 | ContextBuilder 中 System Prompt 明确领域边界；Validator 对输出做二次校验 | `harness/context.py` + `harness/validator.py` |
| SQL 注入 | SQLAlchemy ORM 参数化查询（默认防护） | 全部 DB 查询 |

### 7.3 输出安全

| 防护点 | 措施 |
|--------|------|
| JSON Schema 校验 | 确保 AI 输出结构符合预期，拒绝非法结构 |
| 内容过滤 | Validator 检测输出中的敏感信息模式，标注告警 |
| 导出文件 | 文件名消毒（去除路径遍历字符），限制导出频率 |

## 八、实现计划

### 8.1 开发阶段总览

| 阶段 | 内容 | 产出 |
|------|------|------|
| **S1: 项目脚手架** | 项目初始化、Docker配置、目录结构 | 可启动的空项目 |
| **S2: 数据层** | 数据库模型、种子数据、基础CRUD | 可操作的数据API |
| **S3: Harness 引擎** | 六大模块实现、Agent基类 | 可编排的智能体框架 |
| **S4: 能力画像 Agent** | 四维量化模型、简历解析、雷达图 | 能力画像功能 |
| **S5: 岗位匹配 Agent** | 双向匹配算法、差距分析 | 匹配分析功能 |
| **S6: 路径规划 Agent** | 可解释路径生成、PDF导出 | 路径规划功能 |
| **S7: 职业建议 Agent** | 方向推荐、TOP5输出 | 职业建议功能 |
| **S8: 动态成长追踪** | 任务进度管理、能力值联动、再诊断引擎 | 成长闭环 |
| **S9: 前端界面** | React页面、图表组件、交互流程 | 完整前端 |
| **S10: 导出与集成** | JSON/Excel/PDF导出、全流程联调 | 可演示系统 |
| **S11: 论文与材料** | 技术论文大纲、演示PPT、测试数据 | 比赛材料 |

### 8.2 详细任务拆分

#### S1: 项目脚手架
- [ ] 创建后端 FastAPI 项目结构
- [ ] 创建前端 React + Vite 项目
- [ ] Docker + docker-compose 配置
- [ ] 环境变量与配置管理
- [ ] Git 初始化和 .gitignore

#### S2: 数据层
- [ ] SQLAlchemy ORM 模型定义（Student, Job, DiagnosisResult, TaskProgress, GrowthRecord）
- [ ] 数据库初始化和迁移（Alembic）
- [ ] 种子数据脚本（10+学生, 20+岗位）
- [ ] 学生 CRUD API
- [ ] 岗位 CRUD API

#### S3: Harness 引擎
- [ ] Harness 核心基类设计
- [ ] Orchestrator 流程编排器实现
- [ ] Context Manager 上下文管理器实现
- [ ] Tool Registry 工具注册中心实现
- [ ] Output Validator 输出校验器实现
- [ ] Observer 观测器实现
- [ ] Fallback Manager 容错管理器实现
- [ ] LLM Client 封装（支持多模型切换）

#### S4: 能力画像 Agent
- [ ] 简历解析能力（提取技能/项目/教育信息）
- [ ] 四维能力量化模型实现
- [ ] 能力画像 JSON 生成
- [ ] 雷达图数据格式化
- [ ] 单元测试

#### S5: 岗位匹配 Agent
- [ ] 岗位能力模型解析
- [ ] 双向匹配算法（余弦相似度 + 加权评分）
- [ ] 差距分析引擎
- [ ] TOP5 匹配岗位排序
- [ ] 单元测试

#### S6: 路径规划 Agent
- [ ] 基于差距的路径生成逻辑
- [ ] 阶段目标拆分算法
- [ ] 周任务生成（AI生成 + Harness校验）
- [ ] 可解释性——推理依据标注
- [ ] PDF/Word 路径规划报告导出
- [ ] 单元测试

#### S7: 职业建议 Agent
- [ ] 职业方向推荐引擎
- [ ] 就业指导建议生成
- [ ] 与画像+匹配结果联动
- [ ] 单元测试

#### S8: 动态成长追踪
- [ ] TaskProgress CRUD API
- [ ] GrowthRecord 事件记录
- [ ] 任务完成 → 能力值联动更新引擎
- [ ] 能力变化检测 → 触发再诊断判断逻辑
- [ ] 再诊断 API（复用 Harness 编排，增量更新）
- [ ] 诊断历史链 API（版本对比数据）
- [ ] 能力变化差值计算
- [ ] 单元测试

#### S9: 前端界面（用户向）
- [ ] 项目框架搭建（路由 / 布局 / 主题 / Ant Design）
- [ ] **首页** — Welcome hero + 开始诊断 CTA + 项目介绍
- [ ] **信息输入页** — 简历上传（拖拽+解析）+ 手动信息补全表单 + 目标岗位选择
- [ ] **一站式诊断看板** — 多 Tab 布局（画像 / 匹配 / 路径 / 建议 / 推荐 / 成长）
- [ ] 能力画像 Tab — 雷达图 + 四维分值卡片（标注变化△）+ 技能标签云
- [ ] 岗位匹配 Tab — 匹配度仪表盘 + 差距柱状图 + TOP5（含排名变化↑↓）
- [ ] 成长路径 Tab — 阶段时间线 + 周任务卡片（含 ✓ 标记按钮）+ AI推理依据
- [ ] 职业建议 Tab — 方向推荐卡片 + 动态就业指导文本
- [ ] 就业推荐 Tab — 岗位卡片列表 + 匹配理由 + 变化趋势
- [ ] **成长追踪 Tab** — 诊断历史时间线 + 版本对比视图 + 能力变化曲线图
- [ ] SSE 流式进度展示（步骤进度条 + 实时 AI 处理状态）
- [ ] 再诊断交互 — 任务完成后主动提示 + 一键触发重新诊断
- [ ] 导出工具栏 — JSON / Excel / PDF 一键下载

#### S10: 导出与集成
- [ ] JSON 导出（能力画像）
- [ ] Excel 导出（能力画像 + 匹配结果）
- [ ] PDF 导出（路径规划报告）
- [ ] 全流程端到端测试
- [ ] 响应时间优化（缓存、并行化）
- [ ] Docker 部署验证

#### S11: 论文与材料
- [ ] 技术论文大纲撰写
- [ ] 答辩PPT制作
- [ ] 演示视频脚本
- [ ] 测试案例准备

---

## 九、技术选型依赖

### 9.1 Python 依赖

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
sqlalchemy==2.0.*
pydantic==2.*
openai==1.*
langchain==0.3.*
python-multipart==0.0.*
openpyxl==3.1.*
reportlab==4.*
pytest==8.*
httpx==0.28.*
```

### 9.2 前端依赖

```
react==18.*
react-router-dom==6.*
antd==5.*
echarts==5.*
echarts-for-react==3.*
zustand==5.*
axios==1.*
@ant-design/icons==5.*
typescript==5.*
vite==6.*
```

---

## 十、目录结构总览

```
talent-path/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   ├── core/
│   │   ├── harness/
│   │   ├── agents/
│   │   ├── models/
│   │   └── services/
│   ├── db/
│   ├── config/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
├── README.md
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-30-talent-growth-diagnosis-design.md
```
