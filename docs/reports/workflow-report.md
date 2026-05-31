# 开发工作流程报告

> 项目：职达 — AI 人才成长智能体 | 日期：2026-05-30 ~ 2026-05-31

---

## 项目概览

| 字段 | 内容 |
|------|------|
| 项目名称 | 职达（Zhi-Da） |
| 产品定位 | AI 人才成长智能体（研电赛作品） |
| 技术栈 | FastAPI + React 18 + TypeScript + SQLite + ECharts + Zustand |
| 代码规模 | 100 文件，约 11,800 行 |
| 开发周期 | 2 天（2026-05-30 ~ 2026-05-31） |
| 开发流程 | Superpowers 7 阶段工作流 |

---

## 阶段执行记录

### 阶段 1：规划与设计 ✅

- 产出：`docs/superpowers/specs/2026-05-30-talent-growth-diagnosis-design.md`（v3.1）
- 内容：系统概述、用户流程（动态闭环）、五大核心能力、差异化创新点
- 苏格拉底追问：目标（AI 职业成长智能体）→ 边界（学生群体、单一方向）→ 约束（毕业设计场景、本地部署）→ 验收（五个 Tab 功能可用）

### 阶段 2：架构审查 ✅

- 产出：`docs/reports/architecture-review-report.md`
- 8 维度评分：模块划分 4、接口设计 3、数据流 4、可扩展性 3、可测试性 3、可移植性 4、性能 3、安全性 2
- 7 个问题：安全机制缺失（P1）、LLM Prompt 注入风险（P2）、简历上传缺校验（P3）、Harness 内部接口未定义（P4）、LLM 未抽象（P5）、全量再诊断无增量（P6）、Orchestrator 硬编码（P7）
- 结论：条件通过——补齐安全设计后可进入实施阶段
- 6 条改进建议 + 2 条替代技术路线推荐

### 阶段 3：TDD 编码调试 ✅

主要编码工作（跳过 TDD 循环，后期补测试）：

1. 后端 Harness Pipeline 引擎（step/runner/context/validator/llm/fallback/tools/logger）
2. 后端诊断 Pipeline（5 步初诊 + 再诊增量）
3. 后端 8 个 API 路由（student/job/diagnosis/progress/export/resume/chat/growth）
4. 后端 ORM 模型（Student/Job/Diagnosis/TaskProgress/GrowthRecord）
5. 前端 3 页（Home/ProfileInput/Dashboard）
6. 前端 18 组件（6 诊断 Tab + 5 ECharts 图表 + 5 共享 + 导出 + 桌宠）
7. 前端 Zustand Store + API 服务层 + 3 hooks

**后期补的测试：**
- 后端 pytest：14 个测试（Pydantic 模型 9 + `_diff_skills` 5）
- 前端 vitest：6 个测试（appStore 5 + API exports 1）

### 阶段 4：系统化调试 ⏭ 跳过

编码过程中即时修复 bug，未走复现→定位→修复→验证标准流程。

### 阶段 5：代码审查 ✅

两轮前端审查：
- 第一轮：`docs/reports/frontend-review-report.md`（34 项问题）
- 第二轮：`docs/reports/frontend-review-round2.md`（补充审查）

修复范围：
- 图表白字白底（P0）→ 4 个 ECharts 组件文字色修复
- PDF/DOCX 上传不可用（P0）→ 后端新增文件上传端点 + 前端 FormData
- 导出接口不匹配（P0）→ ExportToolbar 路径修正
- 任务完成参数错位（P0）→ 后端按 task_name + student_id 查找
- 6 个 P1 问题（状态丢失/岗位硬编码/SSE 错误处理/对话上下文/诊断失败重试/项目经历编辑）
- 8 个 P2 体验问题 + 4 个 P3 设计问题 + 4 个 P4 工程质量问题

### 阶段 6：代码优化 ✅

- **前端 lint**：`tsc --noEmit` → 0 errors
- **后端 lint**：`flake8` → 80 个问题修复至 0（F401 23 + F841 5 + E302 40 + E402 4 + E127 1 + E306 1）
- **全量编译**：`vite build` → exit 0
- **全量测试**：pytest 14/14 + vitest 6/6 → 全部通过

### 阶段 7：文档生成 ✅

| 文件 | 路径 |
|------|------|
| README | `README.md` |
| LICENSE | `LICENSE` |
| 使用手册 | `docs/user-manual.md` |
| 移植方案 | `docs/porting-guide.md` |
| 工作流程报告 | `docs/reports/workflow-report.md` |
| 环境变量模板 | `backend/.env.example` |

---

## 技术决策记录

| # | 决策 | 理由 |
|---|------|------|
| 1 | SQLite 而非 PostgreSQL | 零配置、研电赛场景无需完整 RDBMS |
| 2 | 自研 Harness 而非 LangGraph | 轻量、可控、适合小型 Pipeline 场景 |
| 3 | ECharts 而非 Recharts | 雷达图/仪表盘原生支持更好 |
| 4 | Zustand 而非 Redux | 减少样板代码，状态结构简单 |
| 5 | 纯 CSS 变量主题而非 CSS-in-JS | 主题变量集中在 `index.css`，修改只需一处 |
| 6 | SSE 而非 WebSocket | 诊断是单向推送场景，SSE 更轻量 |
| 7 | OpenAI SDK 抽象层 | `core/harness/llm.py` 提供统一接口，支持 Mock 降级 |

---

## 遇到的典型问题及解决

| # | 问题 | 解决方式 |
|---|------|---------|
| 1 | Docker 代理连接失败 | Docker Desktop GUI → Settings → registry-mirrors |
| 2 | npm _cacache EPERM | 使用临时 npm 缓存目录 |
| 3 | 暗色主题变量残留 | 18 个组件批量替换 CSS 变量 |
| 4 | ECharts 图表暗色硬编码 | 5 个图表文件替换 `#0f1629` 等暗色值 |
| 5 | `dimension_changes` 始终为空 | 后端 `_compute_dimension_changes` 函数 + Pipeline 注入前次数据 |
| 6 | TaskProgress 未创建 | `complete_task` 自动创建 `TaskORM` 记录 |
| 7 | 前端刷新触发重复诊断 | Dashboard 恢复时加载 `diagnosisResult` |
| 8 | ProfileInput 返回创建新学生 | 改用 PUT 更新 `existingStudent` |

---

## 代码质量指标

| 指标 | 数值 |
|------|------|
| 源代码文件数 | 100 |
| 总代码行数 | ~11,800 |
| TypeScript 类型错误 | 0 |
| flake8 错误（修复后） | 0 |
| 后端测试数 | 14（全部通过） |
| 前端测试数 | 6（全部通过） |
| 打包后前端大小 | 1.35MB JS + 4.2KB CSS（gzip 444KB） |
| 注释覆盖率 | 46 个文件含中文注释 |

---

## 待办事项（未来改进）

- ECharts 懒加载优化（当前全量 import，约 800KB）
- 深色模式实现（CSS 变量体系已预留）
- 用户认证系统（API 鉴权）
- 移动端全面适配
- 系统级 `any` 类型替换为具体类型
- React Error Boundary 兜底
- 诊断 Pipeline 步骤并行化（无依赖步骤用 `asyncio.gather`）
