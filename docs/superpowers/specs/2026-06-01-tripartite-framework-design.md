# 职达三方协同平台框架重构方案

> 日期：2026-06-01  
> 定位：学校作为可信运营中枢，连接学生诊断结果与企业岗位需求  
> 原则：强化单次诊断决策价值，保留轻量历史记录，不再以长期成长追踪作为主产品叙事

## 一、重构结论

现有学生端不是废弃模块，而是三方协同平台中的“学生诊断工作台”。它已经具备简历解析、能力画像、岗位匹配、差距分析、提升建议和就业推荐能力，可直接复用。

当前缺失的是三方之间的数据流转。新框架将学校端定义为平台运营方：维护课程资源、审核岗位信息、查看群体能力缺口，并在学生授权后向企业推荐人才。企业端负责发布岗位能力模型、查看授权候选人和回填招聘反馈。

## 二、产品信息架构

```text
角色入口 /
├── 学生端 /input → /dashboard
│   ├── 能力画像          主结果
│   ├── 岗位匹配          主结果
│   ├── 职业建议          主结果
│   ├── 就业推荐          主结果
│   ├── 提升建议          次级辅助
│   └── 诊断记录          次级证据链
├── 学校运营端 /school
│   ├── 运营总览          三方状态、培养缺口、待办
│   ├── 课程管理          课程资源与岗位能力映射
│   └── 人才池            按岗位筛选并发起授权推荐
└── 企业招聘端 /enterprise
    ├── 招聘总览          岗位模型、授权人才、反馈状态
    ├── 岗位管理          发布岗位并维护能力要求
    └── 授权候选人        查看授权资料并反馈招聘结果
```

## 三、核心业务闭环

```text
企业发布岗位能力模型
        ↓
学校审核岗位并维护课程能力映射
        ↓
学生上传简历，生成单次诊断报告
        ↓
系统基于岗位模型计算匹配结果
        ↓
学校从人才池发起推荐
        ↓
学生确认授权投递
        ↓
企业查看授权资料并回填面试、录用或拒绝原因
        ↓
学校依据群体短板和招聘反馈优化课程
```

这个闭环满足赛题要求的“可量化、可分析、可优化、可追踪”。其中“可追踪”主要由诊断版本、授权状态和招聘反馈记录承担，不要求把学生端做成重型学习管理系统。

## 四、单次诊断报告

学生端应优先产出一份可被学校和企业共同理解的结构化报告：

| 区域 | 关键信息 | 三方用途 |
|------|----------|----------|
| 能力画像 | 四维评分、优势、短板、证据来源 | 学生理解现状，学校查看共性短板 |
| 岗位匹配 | 匹配度、岗位要求、技能差距、计算依据 | 学生选择方向，企业判断适配度 |
| 职业建议 | 优先补齐项、建议课程、建议项目 | 学校关联课程资源 |
| 就业推荐 | TOP5 岗位、岗位要求、授权投递入口 | 形成推荐与招聘入口 |
| 诊断记录 | 历史版本和变化原因 | 证明结果可追溯 |

`提升建议` 可以保留阶段目标和任务，但定位为诊断报告附录。`诊断记录` 保留复诊历史和证据解释，不再占据主叙事。

## 五、数据模型

在现有 `students`、`jobs`、`diagnosis_results` 基础上增量增加：

```text
schools
id / name / description / created_at

enterprises
id / name / industry / contact / description / created_at

courses
id / school_id / name / description / resources(JSON)
ability_mapping(JSON) / status / created_at

jobs 扩展
enterprise_id / school_review_status / location / salary_range

applications
id / student_id / job_id / school_id / diagnosis_id
match_score / match_detail(JSON) / school_note
student_authorized_at / enterprise_feedback / status / created_at

application_events
id / application_id / event_type / operator_role
description / payload(JSON) / created_at
```

`application_events` 用于留痕，支撑比赛要求中的真实可追溯和可核验。

## 六、API 施工边界

### 学校端

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/school/dashboard` | 获取总览指标 |
| GET/POST/PUT | `/api/school/courses` | 管理课程资源 |
| GET | `/api/school/jobs` | 查看和审核岗位 |
| GET | `/api/school/jobs/{id}/talent-pool` | 查看岗位匹配人才 |
| POST | `/api/school/applications/{id}/recommend` | 发起推荐 |
| GET | `/api/school/applications/{id}/events` | 查看推荐、授权和反馈事件链 |

### 企业端

| 方法 | 路径 | 用途 |
|------|------|------|
| GET/POST/PUT | `/api/enterprise/jobs` | 管理企业岗位 |
| GET | `/api/enterprise/jobs/{id}/candidates` | 查看授权候选人 |
| POST | `/api/enterprise/applications/{id}/feedback` | 回填面试、录用或拒绝状态与招聘反馈 |

### 学生端

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/api/students/{id}/applications` | 查看学校推荐 |
| POST | `/api/students/{id}/applications/{id}/authorize` | 授权投递 |
| POST | `/api/students/{id}/applications/{id}/reject` | 拒绝投递 |

## 七、实施阶段

| 阶段 | 目标 | 验收标准 |
|------|------|----------|
| S1 | 前端多角色框架 | 三个入口可导航，角色职责清晰 |
| S2 | 数据层增量扩展 | 新表可初始化，旧学生端不回归 |
| S3 | 企业端岗位管理 | 企业可创建岗位能力模型 |
| S4 | 学校端人才池 | 学校可按岗位查看匹配学生并推荐 |
| S5 | 学生授权与企业反馈 | 完成推荐、授权、反馈闭环 |
| S6 | 课程能力映射 | 学校可查看课程覆盖缺口 |
| S7 | 案例和答辩材料 | 学生案例、企业案例、可追溯事件链齐全 |

## 八、当前实现状态

本次已完成三方协同平台的后端基础闭环，并保留前端演示框架：

- S1 已完成：首页升级为学生、学校、企业三方入口；学校端和企业端具备分区展示框架；学生端保留现有诊断能力并调整叙事。
- S2 已完成：新增 `schools`、`enterprises`、`courses`、`applications`、`application_events` 表，并通过增量迁移兼容已有 `jobs` 表。
- S3 已完成：企业端 API 支持创建、查询和更新岗位能力模型。
- S4 已完成：学校端 API 支持按具体岗位读取最新诊断中的匹配人才并发起推荐，不再复用学生的全局总分。
- S5 已完成：学生授权接口校验申请归属；企业只能对已授权候选人回填 `interviewed`、`hired` 或 `rejected` 状态和反馈。
- S6 已完成后端统计：学校总览根据已发布课程的 `ability_mapping.jobs` 计算岗位覆盖率。
- S7 已完成后端证据链：推荐、授权、拒绝和企业反馈均写入 `application_events`，学校端可按申请查询事件链。

当前学校端和企业端页面仍使用演示数据，并明确展示“演示框架”标识。后续将门户页面切换到上述 API 后再移除该标识。后端闭环由集成测试覆盖。
