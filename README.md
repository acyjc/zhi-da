# 职达 TalentPath

职达是一个面向高校就业与学生成长场景的三端协同系统。项目重点不是做一个普通简历站，而是围绕"学生档案 -> AI 诊断 -> 成长任务 -> 复评 -> 授权企业查看候选人"的闭环，展示智能体在职业成长辅导中的持续参与能力。

## 核心定位

- 学生端：学生建立档案，上传简历和成绩单，获得 AI 能力诊断、岗位匹配、成长任务和复评结果。
- 企业端：企业维护岗位，提交学校审核，并基于具体岗位查看已授权候选人。
- 学校端：学校作为后台管理方，审核企业、审核岗位、维护系统运行秩序。
- 智能体运行时：统一承接学生侧诊断、追问、任务建议、证据审核、复评和问答。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 后端 | FastAPI, SQLAlchemy async, SQLite (aiosqlite) |
| 智能体 | 统一 Agent Runtime, SSE 流式输出, OpenAI 兼容协议, LLM 可配置降级 |
| 前端 | React 18, TypeScript, Vite, Zustand, Ant Design, ECharts, lucide-react |
| 部署 | Docker Compose, Nginx |
| 测试 | pytest + pytest-asyncio (后端), Vitest + Testing Library (前端) |
| 认证 | PyJWT (HS256), 角色级鉴权 (学生 / 企业 / 管理员) |

## 快速启动

推荐使用 Docker 启动完整环境：

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8000/api/health
```

访问地址：

- 前端：http://localhost
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

健康检查预期返回：

```json
{
  "status": "ok",
  "service": "TalentPath",
  "version": "2.0.0",
  "ai_status": "configured",
  "ai_available": true
}
```

其中 `ai_status` 和 `ai_available` 取决于是否配置了 LLM 密钥（见下文环境变量）。

## 环境变量

在根目录创建 `.env` 文件，Docker Compose 会自动读取：

```env
# 大模型配置（核心，影响 AI 诊断/审核/复评等全部智能体功能）
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini

# 安全配置（生产环境务必修改）
JWT_SECRET=your_random_secret_string

# 管理员账号（学校端登录用）
ADMIN_ACCOUNT=admin
```

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `LLM_API_KEY` | (空) | 大模型密钥，系统核心能力依赖此配置 |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容 API 地址 |
| `LLM_MODEL` | `gpt-4o-mini` | 模型名称 |
| `JWT_SECRET` | 开发默认值 | JWT 签名密钥，生产环境必须修改 |
| `JWT_EXPIRE_MINUTES` | `1440` (24小时) | 会话有效期 |
| `ADMIN_ACCOUNT` | `admin` | 学校管理员账号名 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许跨域的前端地址 |
| `DATABASE_URL` | SQLite 默认路径 | 数据库连接字符串 |

没有 LLM 密钥时，AI 诊断、证据审核、复评等智能体功能不可用，系统会显示"未配置大模型密钥"提示。

## 演示数据

系统在首次启动时自动初始化种子数据，包括 8 家企业和 10 个岗位（含能力模型）。种子数据幂等，重启不会重复创建。

如需重置数据库（清除所有运行时数据并重新初始化），删除 Docker 命名卷后重启：

```bash
docker compose down
docker volume rm agent_talent_path_data
docker compose up -d --build
```

## 演示账号

### 企业端

| 企业 ID | 名称 | 状态 | 用途 |
| --- | --- | --- | --- |
| `1` | 测试企业：字节跳动 | 正常 | 演示正常企业全流程 |
| `2` | 测试企业：阿里巴巴 | 正常 | 演示岗位审核流程 |
| `4` | 测试企业：已禁用公司 | 禁用 | 演示企业门禁拦截 |
| `3` | 测试企业：待审核公司 | 待审核 | 演示待审核状态 |
| `5` | 华为技术 | 正常 | 含完整岗位能力模型 |
| `6` | 腾讯科技 | 正常 | 含两个岗位 |
| `7` | 美团 | 正常 | 含推荐算法岗位 |
| `8` | 小米科技 | 正常 | 含移动开发岗位 |

### 学校端

| 账号 | 说明 |
| --- | --- |
| `admin` | 管理员账号（可通过 `ADMIN_ACCOUNT` 环境变量修改） |

### 学生端

学生通过前端"新用户"入口注册创建，无需预置账号。建议使用以下流程演示：

1. 在前端首页选择"学生端"。
2. 点击"新用户"进入空白档案。
3. 填写教育背景、技能、项目经历等信息。
4. 保存后自动进入诊断流程。

当前版本登录只做角色和用户区分，密码框保留用于后续扩展。

## 主流程

```text
新学生进入
  -> 创建档案 / 上传简历 / 补充核心字段
  -> Agent 判断信息是否完整
  -> 生成能力诊断（SSE 流式进度反馈）
  -> 匹配已审核岗位（TOP5 排行 + 差距分析）
  -> 生成成长任务（分阶段路径规划）
  -> 学生提交证据
  -> Agent 审核证据
  -> 触发复评（能力变化量化对比）
  -> 学生授权企业查看
  -> 企业按岗位查看授权候选人
```

## 三端功能

### 学生端

- 新用户注册和已有学生登录
- 学生档案维护（教育背景、技能、项目经历、学业基础、软技能证据）
- 简历上传与 AI 解析（支持 PDF / DOCX / TXT，LLM 自动提取结构化数据）
- 成绩单上传（仅作为企业查看材料，不做自动识别）
- AI 诊断与解释性结果展示（五维能力画像、匹配分公式解释、置信度）
- 岗位匹配与差距分析（TOP5 岗位排行、技能差距柱状图）
- 成长任务、证据提交、AI 审核、复评（版本间能力变化对比）
- 授权企业查看个人画像和材料
- AI 助手对话（悬浮按钮，支持自然语言问答）
- 导出诊断报告（PDF / Excel）

### 企业端

- 企业登录门禁（待审核/已禁用企业自动拦截）
- 岗位列表和岗位状态管理（已发布 / 待审核 / 已下线）
- 创建岗位、AI 解析岗位能力模型、提交学校审核
- 查看审核驳回原因
- 基于岗位查看已授权候选人
- 查看候选人画像、匹配分、优势、差距和证明材料

### 学校端

- 概览统计面板（学生数、企业数、已审核岗位数、待审核岗位数，可点击跳转）
- 企业管理（审核/启用/禁用企业）
- 岗位审核（通过/驳回，查看招聘要求描述和能力模型）
- 学生信息查看
- 退出登录功能

## 测试

后端（204 个测试用例）：

```bash
docker compose exec -T backend python -m pytest
```

前端：

```bash
cd frontend
npx vitest run
npm run build
```

## 项目结构

```text
backend/
  api/routes/          后端接口（auth, student, enterprise, admin, agent, diagnosis, ...）
  core/agent/          统一智能体运行时（runtime, skills, tools, stream）
  core/services/       业务服务（diagnosis, student, growth_tasks）
  core/models/         请求/响应数据模型
  core/auth.py         JWT 认证与鉴权
  config/settings.py   环境变量与配置
  db/                  ORM 模型与数据库连接（含种子数据初始化）
  tests/               后端测试（204 个用例）

frontend/
  src/pages/           三端页面（Dashboard, ProfileInput, EnterpriseDashboard, AdminDashboard）
  src/pages/Dashboard/ Tab 组件（OverviewTab, DiagnosisTab, TasksTab, AuthorizationPageTab）
  src/components/      业务组件（diagnosis, charts, export, shared）
  src/services/        API 客户端（axios + JWT 拦截）
  src/stores/          前端状态（Zustand）
  src/types/           TypeScript 类型定义

docs/
  user-manual.md       使用手册
  demo-walkthrough.md  演示流程
```

## Git 注意事项

以下内容不会上传（已在 `.gitignore` 中排除）：

- `.env`（密钥配置）
- 数据库文件（`*.db`, `*.sqlite3`）
- `uploads/`（用户上传文件）
- `node_modules/` / `dist/`（前端依赖和构建产物）
- `artifacts/` / `local-process-docs/`（过程文档）
- `__pycache__/` / `.pytest_cache/`（Python 缓存）

过程报告、临时审查、开发记录请放入 `local-process-docs/`。
