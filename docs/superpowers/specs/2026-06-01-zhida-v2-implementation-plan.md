# 职达 V2 产品落地改造方案

> 日期：2026-06-01  
> 适用范围：学生成长诊断与路径规划方向  
> 本轮目标：将现有演示原型升级为一版逻辑可信、可持续迭代的产品  
> 暂不纳入：登录、角色鉴权、租户隔离、生产级安全治理

## 一、改造结论

职达不是三套独立系统，也不应做成一套页面强行兼容三个角色。

正确形态是：

> 一套职达平台，三个角色工作空间，一套复用设计系统，三套独立信息架构。

三端可以复用品牌、布局骨架、基础组件和交互规范，但必须根据用户目标重新组织页面内容：

| 端 | 用户核心问题 | 页面形态 | 使用频率 |
|----|--------------|----------|----------|
| 学生端 | 我下一步做什么，如何更接近目标岗位？ | 行动导向、轻量、强调成长反馈 | 高频 |
| 企业端 | 我的岗位有哪些已授权候选人，如何反馈？ | 表格导向、效率优先、强调岗位流转 | 中频 |
| 学校端 | 哪些数据或流程需要后台处理？ | 管理后台、异常优先、强调运营治理 | 低频 |

学校端不再承担人才推荐。岗位匹配由系统自动执行，学生自主决定是否授权投递。

## 二、统一设计系统与角色差异

### 2.1 可复用范围

以下元素应在三端复用，避免重复开发：

| 类型 | 复用内容 |
|------|----------|
| 品牌 | 职达 Logo、字体、基础间距、圆角、阴影、图标语言 |
| 页面骨架 | 侧边导航、页面标题、指标卡、内容卡片、表格、空状态 |
| 基础组件 | `StatusBadge`、`MetricCard`、`DataTable`、`FilterBar`、`EmptyState`、`Timeline`、`Modal`、`Toast` |
| 表单组件 | 输入框、选择器、标签编辑器、分值条、步骤条、提交状态 |
| 业务组件 | 岗位卡片、匹配分、证据列表、反馈时间线、任务卡片 |
| 设计变量 | 背景色、文本色、边框色、成功/警告/错误状态色 |

### 2.2 角色差异

角色差异不依赖完全不同的组件，而依赖主题色、信息架构和内容密度：

| 端 | 主色 | 视觉语义 | 页面重点 |
|----|------|----------|----------|
| 学生端 | 蓝紫色 `#5B7BB5` | 成长、方向、陪伴 | 当前目标、本周行动、职达建议 |
| 学校端 | 青绿色 `#5A9E8F` | 稳定、治理、可信 | 待处理事项、学生列表、岗位审核 |
| 企业端 | 琥珀色 `#C4944A` | 招聘、机会、结果 | 岗位管理、授权候选人、反馈 |

建议将主题配置抽离为统一对象：

```ts
export const workspaceThemes = {
  student: {
    accent: 'var(--accent-blue)',
    roleLabel: '学生成长端',
  },
  school: {
    accent: 'var(--accent-teal)',
    roleLabel: '学校管理后台',
  },
  enterprise: {
    accent: 'var(--accent-amber)',
    roleLabel: '企业招聘端',
  },
}
```

### 2.3 页面外壳策略

保留现有 `PortalWorkspace` 思路，但将其升级为更通用的 `WorkspaceShell`：

```text
WorkspaceShell
├── 品牌区
├── 角色标识
├── 侧边导航
├── 页面标题
├── 指标卡槽位
├── 内容区域
└── 通用反馈组件
```

学生端可以复用基础组件，但不建议直接复用学校和企业的后台外壳。学生端需要更轻、更有行动感的 `StudentShell`：

```text
StudentShell
├── 品牌导航
├── 成长状态
├── 职达建议入口
├── 主内容
└── 职达小喵
```

学校端和企业端共用 `WorkspaceShell`，通过主题色和导航配置区分。

## 三、三端页面信息架构

### 3.1 学生端

路由建议：

```text
/student
├── /home             职达首页
├── /explore          方向探索
├── /profile          能力画像
├── /plan             进阶路径
├── /opportunities    职达机会
├── /growth           成长轨迹
└── /advisor          职达顾问
```

现有 `/input` 可保留为首次建档流程，现有 `/dashboard` 逐步拆分为以上子页面。

#### 职达首页

首页不再是功能 Tab 集合，而是行动首页：

| 区域 | 必须展示 |
|------|----------|
| 当前目标 | 主目标岗位、匹配度、最近变化 |
| 本周进阶 | 1–3 个可执行任务、预计耗时、提交标准 |
| 职达建议 | 当前最值得处理的一条主动建议 |
| 待补能力 | 优先级最高的 3 个能力差距 |
| 职达机会 | 立即可投递、短期可争取的数量 |
| 最近进展 | 新证据、任务完成、企业反馈 |

#### 方向探索

学生可以不填写目标岗位。系统根据简历、兴趣和时间预算生成 3 个候选方向：

```text
方向名称 + 基础适配度 + LLM 解释 + 关键短板 + 补齐周期 + 当前机会数
```

学生选择一个主目标和最多两个备选目标。

#### 能力画像

所有评分必须展示：

```text
分数 + 置信度 + 证据来源 + 仍缺少的证据
```

禁止只展示无法解释的 AI 分值。

#### 进阶路径

路径分为两层：

```text
长期阶段目标：帮助学生理解方向
本周滚动任务：帮助学生立刻行动
```

每个任务必须持久化，刷新后不可丢失。

#### 职达机会

取消“学校推荐岗位”的叙事。机会按学生行动成本分组：

```text
立即可投递
短期可争取
长期成长方向
```

#### 职达顾问

职达小喵和顾问页共享同一套后端上下文能力：

```text
学生画像 + 证据 + 主目标 + 备选目标 + 本周任务 + 机会 + 企业反馈
```

桌宠负责轻量主动提醒，顾问页负责完整对话。

### 3.2 学校管理后台

路由建议：

```text
/school
├── /overview         运营总览
├── /students         学生管理
├── /partners         企业与岗位
└── /feedback         反馈记录
```

学校端只承担连接桥梁和后台治理职责。

#### 运营总览

只展示需要学校处理的事项：

| 指标 | 操作 |
|------|------|
| 待审核岗位 | 进入岗位审核 |
| 资料不完整学生 | 进入学生列表并筛选 |
| 长期未活跃学生 | 发送提醒 |
| 待补充企业反馈 | 查看反馈记录 |
| 高频能力缺口 | 了解整体情况 |

#### 学生管理

必须新增学生列表：

| 字段 | 说明 |
|------|------|
| 姓名、专业、年级 | 基础识别 |
| 主目标岗位 | 判断方向 |
| 诊断状态 | 未诊断、待补充、已完成 |
| 最近诊断时间 | 判断是否过期 |
| 最高匹配岗位和分数 | 快速了解状态 |
| 投递状态 | 未投递、已授权、面试中、已录用 |
| 最近活跃时间 | 判断是否需要提醒 |
| 操作 | 查看详情、提醒、异常标记 |

学生详情只展示运营必要信息，不扩展为复杂教务档案。

#### 企业与岗位

合并企业管理和岗位审核。学校可以：

- 查看合作企业
- 审核岗位
- 下线异常岗位
- 查看岗位匹配情况摘要

学校不可：

- 手工筛选人才
- 点击“推荐岗位”
- 修改学生匹配分
- 替学生授权

#### 反馈记录

展示系统匹配到招聘反馈的事件时间线：

```text
系统匹配 → 学生授权 / 暂不考虑 → 企业查看 → 面试 → 录用 / 拒绝
```

### 3.3 企业招聘端

路由建议：

```text
/enterprise
├── /overview         招聘总览
├── /jobs             岗位管理
└── /candidates       授权候选人
```

#### 招聘总览

展示：

- 开放岗位数量
- 待完善岗位模型
- 新增授权候选人
- 待反馈候选人
- 已录用人数

#### 岗位管理

发布流程改为：

```text
粘贴 JD
    ↓
LLM 提取岗位能力模型
    ↓
企业确认和调整
    ↓
提交学校审核
    ↓
审核通过后进入自动匹配
```

岗位模型包括：

```text
技术能力 + 项目经验 + 软技能 + 领域知识 + 四维权重
```

#### 授权候选人

企业只查看已授权候选人。候选人 DTO 必须包含真实的脱敏字段：

```text
display_name
major
grade
match_score
match_detail
application_status
authorized_at
```

禁止继续使用固定姓名、固定专业或 `school_note` 作为展示兜底。

## 四、删除和替换现有功能

| 当前功能 | 处理方式 | 原因 |
|----------|----------|------|
| 学校端课程管理 | 暂时移除导航，可保留代码 | 当前不是核心闭环 |
| 学校端人才池手工推荐 | 删除 | 与自动匹配原则冲突 |
| `recommended` 状态 | 替换为 `matched` | 机会来源应为系统匹配 |
| `school_note` | 弱化或移除 | 学校不再参与推荐 |
| 前端硬编码差距解释 | 删除 | 会损害用户信任 |
| 前端硬编码 GitHub 仓库 | 删除 | 资源必须可访问、可核验 |
| 前端临时 `customTasks` | 替换为后端任务 API | 刷新后任务不可丢失 |
| 固定企业候选人姓名和专业 | 替换为候选人 DTO | 当前展示不真实 |
| 小喵固定快捷问题 | 替换为上下文快捷建议 | 桌宠应感知当前页面和成长状态 |

## 五、核心状态机调整

### 5.1 机会状态

```text
matched       系统自动匹配，学生可查看
authorized    学生授权投递
ignored       学生暂不考虑
viewed        企业已查看
interviewed   进入面试
hired         企业录用
declined      企业拒绝
```

状态流转：

```text
matched
├── authorized → viewed → interviewed → hired
│                              └──────→ declined
└── ignored
```

### 5.2 任务状态

```text
pending       待开始
in_progress   进行中
submitted     已提交证据
verified      已核验
adjusted      已被新计划替代
```

## 六、数据模型增量改造

### 6.1 调整 `applications`

保留：

```text
id
student_id
job_id
diagnosis_id
match_score
match_detail
status
student_authorized_at
enterprise_feedback
created_at
```

弱化或移除：

```text
school_id
school_note
recommended
```

### 6.2 新增 `growth_tasks`

```text
id
student_id
diagnosis_id
source_type(gap|feedback|advisor|manual)
source_ref_id
title
description
steps(JSON)
resource_links(JSON)
evidence_requirement
skill_impact(JSON)
estimated_minutes
estimated_gain_range(JSON)
status
created_at
updated_at
```

### 6.3 新增 `student_evidence`

```text
id
student_id
task_id
evidence_type(resume|answer|project|course|certificate|task|enterprise_feedback)
title
content
source_url
skill_mapping(JSON)
confidence
verified_status
created_at
```

### 6.4 可后置表

以下能力有价值，但可在第二轮建设：

- `agent_questions`
- `agent_runs`
- `student_targets`
- `resource_catalog`

## 七、API 改造清单

### 7.1 学生端

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/students/{id}/workspace` | 聚合职达首页 |
| POST | `/api/students/{id}/explore` | 生成方向探索建议 |
| GET | `/api/students/{id}/profile` | 获取画像、证据和置信度 |
| GET | `/api/students/{id}/tasks` | 获取本周任务 |
| POST | `/api/students/{id}/tasks` | 将建议持久化为任务 |
| POST | `/api/students/{id}/tasks/{task_id}/evidence` | 提交任务证据 |
| GET | `/api/students/{id}/opportunities` | 获取自动匹配机会 |
| POST | `/api/students/{id}/opportunities/{id}/authorize` | 学生授权 |
| POST | `/api/students/{id}/opportunities/{id}/ignore` | 暂不考虑 |
| POST | `/api/students/{id}/advisor` | 带学生上下文的顾问对话 |

### 7.2 企业端

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/api/enterprise/jobs/parse-jd` | LLM 提取岗位模型 |
| GET/POST/PUT | `/api/enterprise/jobs` | 岗位管理 |
| GET | `/api/enterprise/jobs/{id}/candidates` | 返回脱敏候选人 DTO |
| POST | `/api/enterprise/applications/{id}/feedback` | 提交招聘反馈 |

### 7.3 学校端

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/school/dashboard` | 运营总览 |
| GET | `/api/school/students` | 学生管理列表 |
| GET | `/api/school/students/{id}` | 学生运营详情 |
| POST | `/api/school/students/{id}/remind` | 发送提醒 |
| GET | `/api/school/jobs` | 岗位审核列表 |
| PUT | `/api/school/jobs/{id}/review` | 审核岗位 |
| GET | `/api/school/applications` | 反馈记录 |
| GET | `/api/school/applications/{id}/events` | 查看事件链 |

## 八、LLM 与规则算法职责

### 8.1 LLM 参与位置

| 场景 | LLM 输入 | LLM 输出 |
|------|----------|----------|
| 简历解析 | 简历文本 | 结构化学生档案 |
| 方向探索 | 学生画像、偏好、岗位库 | 3 个候选方向和解释 |
| JD 解析 | 企业 JD | 岗位能力模型草案 |
| 差距解释 | 规则差距、证据 | 个性化原因和缺失证据 |
| 任务生成 | 差距、时间预算、资源目录 | 1–3 个任务草案 |
| 顾问对话 | 学生完整上下文 | 可执行建议 |
| 企业拒绝反馈 | 反馈、当前路径 | 新任务或计划调整建议 |

### 8.2 规则算法负责

- 四维能力基础分
- 岗位要求权重
- 基础匹配度
- 差距排序
- 任务完成后的能力影响区间
- 机会分类阈值

### 8.3 可信度要求

页面不得将前端静态模板包装成 AI 结果。

每条 AI 内容应带：

```text
生成来源
依赖证据
生成时间
置信度
是否经过用户确认
```

资源链接只能来自：

- 学校已维护课程
- 系统资源目录
- 经过可访问性检查的公开链接
- 企业提供的岗位相关材料

## 九、前端代码改造建议

### 9.1 组件目录

```text
frontend/src/
├── components/
│   ├── shell/
│   │   ├── WorkspaceShell.tsx
│   │   └── StudentShell.tsx
│   ├── ui/
│   │   ├── MetricCard.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── DataTable.tsx
│   │   ├── EmptyState.tsx
│   │   ├── Timeline.tsx
│   │   └── Toast.tsx
│   ├── student/
│   │   ├── WeeklyTaskCard.tsx
│   │   ├── OpportunityCard.tsx
│   │   ├── EvidenceList.tsx
│   │   └── AdvisorPanel.tsx
│   ├── school/
│   │   ├── StudentTable.tsx
│   │   ├── JobReviewTable.tsx
│   │   └── FeedbackTimeline.tsx
│   └── enterprise/
│       ├── JobEditor.tsx
│       ├── CandidateTable.tsx
│       └── FeedbackModal.tsx
```

### 9.2 当前文件调整

| 文件 | 调整 |
|------|------|
| `frontend/src/components/portal/PortalWorkspace.tsx` | 重命名并升级为 `WorkspaceShell` |
| `frontend/src/pages/Dashboard.tsx` | 拆分学生首页、画像、路径、机会和轨迹 |
| `frontend/src/pages/SchoolPortal.tsx` | 删除课程管理和人才推荐，新增学生列表和反馈记录 |
| `frontend/src/pages/EnterprisePortal.tsx` | 增加 JD 智能解析，使用候选人 DTO |
| `frontend/src/components/shared/ActionDrawer.tsx` | 改为读取后端生成的差距解释、资源和收益区间 |
| `frontend/src/components/SalaryCat/SalaryCat.tsx` | 传入 `student_id`、页面场景和建议上下文 |
| `frontend/src/services/api.ts` | 按学生、学校、企业领域拆分 API 模块 |

## 十、实施顺序

### 阶段 0：移除错误叙事

目标：先消除会误导用户的内容。

- 删除学校端“推荐岗位”按钮
- 页面文案统一改为“系统匹配”
- 删除固定 GitHub 仓库链接
- 删除前端静态 AI 差距解释
- 删除固定候选人姓名和专业兜底
- 将 `recommended` 文案替换为 `matched`

验收标准：

- 页面不再出现“学校向学生推荐岗位”
- 页面不再把前端模板称为 AI 结果
- 企业候选人列表不显示伪造字段

### 阶段 1：打通真实机会闭环

目标：完成最小可用三方流程。

```text
企业发布岗位 → 学校审核 → 系统自动匹配 → 学生授权 → 企业反馈
```

- 调整 `applications` 状态机
- 岗位审核通过后触发自动匹配
- 学生端展示自动匹配机会
- 企业候选人接口返回真实脱敏 DTO
- 企业反馈写入事件链

验收标准：

- 无需学校手工推荐即可完成整条流程
- 学生可授权或暂不考虑
- 企业只看到已授权候选人
- 每个状态都有事件记录

### 阶段 2：任务持久化与证据链

目标：让成长路径从演示卡片变成真实可持续功能。

- 新增 `growth_tasks`
- 新增 `student_evidence`
- 将差距侧边栏接入任务创建 API
- 任务完成时提交证据
- 页面展示能力项的证据来源和置信度
- 企业拒绝反馈转换为任务草案

验收标准：

- 刷新页面后任务仍存在
- 每个能力分可查看证据
- 企业拒绝后能生成可确认的新任务

### 阶段 3：职达顾问上下文化

目标：让用户明显感知智能体能力。

- 顾问接口接收 `student_id` 和 `scene`
- 后端构建学生上下文
- 小喵快捷问题根据页面动态变化
- 首页展示主动建议
- 任务停滞、资料不足、新机会和企业反馈触发提醒

验收标准：

- 顾问可以解释学生的具体分数和任务
- 在画像、路径、机会页面展示不同快捷建议
- 顾问不再只给通用职业建议

### 阶段 4：三端页面重构

目标：形成统一但不混淆的三端体验。

- 建立共享设计系统
- 学生端拆分行动首页和业务子页
- 学校端新增学生管理列表
- 学校端弱化课程管理
- 企业端增加 JD 智能提取
- 按路由懒加载页面和图表组件

验收标准：

- 三端品牌一致、主题色明确
- 学校和企业复用后台外壳
- 学生端突出行动，不呈现后台感
- 构建产物完成按页面拆包

## 十一、测试与验收清单

### 11.1 API 测试

- 岗位审核通过后自动生成 `matched` 机会
- 学生授权后企业候选人接口可见
- 学生暂不考虑后企业候选人接口不可见
- 企业反馈后事件链新增记录
- 企业拒绝后生成任务草案
- 任务创建、刷新、提交证据和核验状态可用
- 顾问可以读取学生当前画像和任务

### 11.2 前端测试

- 学生未填写目标岗位也可进入方向探索
- 小喵只在学生端展示
- 学校端没有手工推荐入口
- 学校端可以查看学生列表
- 企业端候选人不显示固定兜底内容
- 差距侧边栏不展示硬编码 AI 文案
- 三端主题色正确
- 页面刷新后任务仍存在

### 11.3 产品验收

用一个学生、一家企业和一个岗位完成完整流程：

```text
学生上传简历
→ 系统诊断并给出方向
→ 企业发布岗位
→ 学校审核岗位
→ 系统自动匹配
→ 学生查看依据并授权
→ 企业查看脱敏候选人并拒绝，填写 Docker 经验不足
→ 学生端收到反馈
→ 职达生成 Docker 进阶任务
→ 学生提交证据
→ 能力画像和机会匹配更新
```

该流程跑通后，职达才具备第一版产品闭环。

## 十二、本轮建议范围

如果目标是尽快做出一版可信产品，建议本轮优先完成：

```text
阶段 0：移除错误叙事
阶段 1：真实机会闭环
阶段 2：任务持久化与证据链
```

阶段 3 和阶段 4 可以在闭环可用后继续迭代，但共享设计系统应从本轮开始建立，避免后续重复修改页面。
