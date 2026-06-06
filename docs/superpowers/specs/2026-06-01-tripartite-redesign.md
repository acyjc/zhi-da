# 职达 — 三方协同智能体平台 重设计方案

> 产品定位：面向高校就业与人才培养场景的三方协同智能体平台
> 核心原则：学校作为可信中枢，连接学生成长数据与企业岗位需求

---

## 一、业务流程图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         完整推荐闭环                                │
│                                                                     │
│  ┌──────────┐         ┌──────────┐         ┌──────────┐            │
│  │  企业端   │  ①发布  │  AI引擎  │  ④推荐  │  学校端   │            │
│  │          │────────▶│          │◀────────│          │            │
│  │ 岗位发布  │         │ 能力画像  │         │ 人才池    │            │
│  │ 查看候选人│         │ 匹配计算  │         │ 群体分析  │            │
│  │ 面试反馈  │         │ 路径规划  │         │ 教学建议  │            │
│  │ 录用/拒绝 │         │ 就业推荐  │         │ 就业预警  │            │
│  └────┬─────┘         └────┬─────┘         └────┬─────┘            │
│       │                    │                    │                  │
│       │   ⑦查看授权资料    │   ②自动匹配        │                  │
│       │   ⑧反馈结果        │                    │                  │
│       │◀───────────────────┼───────────────────▶│                  │
│       │                    │                    │                  │
│       │                    │   ③匹配通知        │                  │
│       │                    │◀───────────────────│                  │
│       │                    │                    │                  │
│       │                    │   ⑤授权请求        │                  │
│       │                    │───────────────────▶│                  │
│       │                    │                    │       ⑥确认授权  │
│       │                    │               ┌──────────┐            │
│       │                    │               │  学生端   │            │
│       │                    │               │ 授权投递  │            │
│       │                    │               │ 拒绝授权  │            │
│       │                    │               └──────────┘            │
└─────────────────────────────────────────────────────────────────────┘

流程步骤：
① 企业发布岗位（岗位名称 + 技能要求 + 权重配置 + JD描述）
② 系统自动对所有学生计算该岗位的匹配度（基于四维能力画像）
③ 学校查看匹配结果 → 筛选人才池
④ 学校对合适的学生发起"推荐"
⑤ 学生收到推荐通知 → 查看岗位详情 + 自己的匹配依据
⑥ 学生确认授权（或拒绝）
⑦ 企业查看授权后的学生列表（画像 + 匹配依据 + 学校推荐意见）
⑧ 企业反馈：面试 / 录用 / 婉拒（附原因）
```

## 二、数据模型

### 新增表

**users** — 三端统一账户
```
id / username / password_hash / role(学生|学校|企业) / name / email / created_at
关联：role=学生→students.id, role=企业→enterprises.id
```

**enterprises** — 企业信息
```
id / name / industry / size / description / contact / user_id(FK→users)
```

**schools** — 学校信息
```
id / name / user_id(FK→users)
```

**jobs(重构)** — 岗位表（企业发布）
```
id / title / description / enterprise_id / requirements(JSON) / weight_config(JSON)
status(open|closed|filled) / location / salary_range / posted_by / created_at

requirements 结构：
{
  "tech_skills": {"Python": 80, "Django": 75},
  "soft_skills": {"沟通表达": 70},
  "domain_knowledge": {"后端开发": 80},
  "education": "本科及以上",
  "experience": "1年以上"
}
```

**applications** — 核心状态表（全程留痕可追溯）
```
id / job_id(FK)     / student_id(FK)    / school_id
match_score / match_detail(JSON) / school_note / enterprise_feedback

status 枚举：
  matched     → 系统自动匹配
  recommended → 学校推荐
  authorized  → 学生授权
  rejected    → 学生拒绝
  viewed      → 企业已查看
  interviewed → 进入面试
  offered     → 发放offer
  declined    → 企业婉拒

status_changed_at / created_at
```

### 现有表变更

| 表 | 变更 |
|------|------|
| `students` | 新增 `school_id`(FK→schools)、`user_id`(FK→users，可选) |
| `jobs`(旧) | 保留作为系统预设模板 |
| `diagnosis_results`/`task_progress`/`growth_records` | 不变 |

## 三、API 路由

### 企业端 `/api/enterprise`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/enterprise/login` | 登录 |
| POST | `/api/enterprise/jobs` | 发布岗位 |
| GET | `/api/enterprise/jobs` | 我的岗位 |
| GET | `/api/enterprise/jobs/{id}` | 岗位详情 |
| PUT | `/api/enterprise/jobs/{id}` | 编辑岗位 |
| GET | `/api/enterprise/jobs/{id}/candidates` | 授权候选人(含匹配详情) |
| POST | `/api/enterprise/applications/{id}/feedback` | 面试/录用/婉拒 |

### 学校端 `/api/school`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/school/login` | 登录 |
| GET | `/api/school/jobs` | 所有开放岗位 |
| GET | `/api/school/jobs/{id}/talent-pool` | 该岗位匹配学生(按匹配度排序) |
| POST | `/api/school/recommend` | 推荐学生(job_id+student_id+note) |
| GET | `/api/school/dashboard` | 数据总览 |
| GET | `/api/school/students/overview` | 群体能力分布 |
| GET | `/api/school/students/warning` | 就业预警(匹配<40%) |

### 学生端新增

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/students/{id}/applications` | 我的推荐列表 |
| POST | `/api/students/{id}/applications/{app_id}/authorize` | 授权 |
| POST | `/api/students/{id}/applications/{app_id}/reject` | 拒绝 |

## 四、前端页面

```
首页(角色选择)
├── 学生端 /student（保留现有全部 6 Tab 诊断看板）
│   └── +Dashboard 顶部推荐通知条 + 详情弹窗
├── 学校端 /school（全新）
│   ├── 数据总览（ECharts：群体画像/匹配率/就业率）
│   ├── 人才池（按岗位筛学生+推荐操作）
│   └── 就业预警（低分学生名单）
└── 企业端 /enterprise（全新）
    ├── 岗位管理（发布/编辑/关闭）
    ├── 候选人列表（授权后可见）
    └── 反馈操作（面试/录用/婉拒+原因）
```

## 五、复用 vs 新建

| 复用(保留) | 新建 |
|------------|------|
| 学生端诊断看板 6 Tab 全部 | users 表 + 3 个登录接口 |
| Pipeline 引擎 | enterprises/schools 表 |
| 简历解析 | jobs 表重构 |
| LLM 客户端(DeepSeek) | applications 核心表(7状态) |
| 桌宠 | 企业端 7 API + 3 页面 |
| 导出 | 学校端 7 API + 3 页面 |
| 全部测试 | 学生端新增 3 API + 通知UI |

## 六、施工顺序

```
S1: 数据层——users/enterprises/schools/jobs(重构)/applications 表
S2: 认证——3 个登录接口 + 前端首页角色选择
S3: 企业端——岗位管理 + 候选人列表 + 反馈
S4: 学校端——总览看板 + 人才池 + 推荐 + 预警
S5: 学生端增强——推荐通知条 + 授权/拒绝
S6: 联调——端到端流程验证
```
