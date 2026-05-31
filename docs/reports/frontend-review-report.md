# 🔍 「职达」全方位忠实用户审查报告

> 项目定位：AI 人才成长智能体——上传简历 → AI 解析 → 能力画像 → 岗位匹配 → 成长路径 → 持续追踪
> 技术栈：React 18 + TypeScript + Vite + ECharts + Zustand / FastAPI + SQLite + LLM
> 审查范围：前端全部页面/组件/图表/hooks/状态/API 层 + 后端全部路由/模型/服务 + 部署配置

---

## 一、🔴 致命问题（必须立即修复）

### 1. 图表核心数据完全不可读——白字白底

这是用户第一眼就会看到的 bug，直接摧毁产品专业感。

| 文件 | 问题 |
|------|------|
| `RadarChart.tsx:91` | tooltip `textStyle.color: '#e2e8f0'`（浅灰白），背景 `rgba(248,247,244,0.95)`（近白），白字白底完全看不清 |
| `MatchGauge.tsx:125` | 仪表盘中心百分比 `detail.color: '#e2e8f0'`，浅色背景上核心匹配度数字完全不可读 |
| `GapBar.tsx:34` | tooltip 同样白字白底 |
| `GrowthTrend.tsx:75` | tooltip 同样白字白底 |

**影响**：用户最关心的匹配度分数、能力分值、差距数据全部看不清。这是产品最核心的数据展示层。

### 2. PDF/DOCX 简历上传功能名存实亡

`ProfileInput.tsx:79` 使用 `reader.readAsText(file)` 读取用户上传的文件。这个 API 只能正确读取纯文本文件，对 PDF 和 DOCX 会输出乱码或空内容。

而后端 `resume.py` 的解析接口只接受 `resume_text` 文本参数，没有文件上传端点。后端 `settings.py` 虽然定义了 `UPLOAD_DIR` 和 `ALLOWED_UPLOAD_TYPES`，但从未被使用。

**影响**：用户上传 PDF/DOCX 简历（最常见场景）时，AI 解析收到的是乱码，要么解析失败，要么得到错误结果。前端还显示了"支持 PDF / DOCX / TXT"的误导提示。

### 3. 导出功能前后端接口不匹配

前端 `ExportToolbar.tsx:28` 调用：
```
/api/export/json?student_id=...&diagnosis_id=...
/api/export/excel?student_id=...&diagnosis_id=...
/api/export/pdf?student_id=...&diagnosis_id=...
```

但后端 `export.py` 实际的端点是：
- `GET /api/export/profile/{student_id}` → JSON
- `GET /api/export/profile/{student_id}/excel` → Excel
- `GET /api/export/path/{student_id}` → PDF

路径结构、参数方式完全不同，三个导出按钮全部会 404。

### 4. 任务完成接口参数不匹配

前端 `PathTab.tsx:38` 调用 `completeTask({ student_id, task_id: taskName, evidence: '' })`，其中 `task_id` 传的是任务的名称字符串。

但后端 `progress.py:16` 用 `TaskORM.id` 查找任务（`select(TaskORM).where(TaskORM.id == req.task_id)`），这是一个 8 位 UUID。用任务名称去查 UUID，永远找不到任务，返回 `{"success": false, "error": "Task not found"}`。

**影响**：成长路径中"标记完成"功能完全无法使用。

---

## 二、🟠 严重问题（严重影响用户体验）

### 5. 没有用户身份系统——数据随时丢失

当前 `student_id` 仅存在 `localStorage` 中（`ProfileInput.tsx:153`），换浏览器、清缓存、换设备就丢失全部诊断数据。对于忠实用户来说，积累的成长记录是最有价值的资产。

更严重的是，Dashboard 页面刷新后 `student` 为 null，只显示"请先填写个人信息"，但不会尝试从 `localStorage` 恢复会话。

### 6. 岗位列表硬编码，未使用后端数据

`ProfileInput.tsx:24` 硬编码了 5 个岗位：
```typescript
const jobOptions = ['Python后端开发工程师', 'AI算法工程师', '前端开发工程师', '数据分析师', '产品经理']
```

而后端 `seed.py` 已有完整的岗位数据，`job.py` 也提供了 `GET /api/jobs` 接口。Dashboard 中调用了 `listJobs()`，但 ProfileInput 没有。如果后端新增岗位，前端不会同步。

### 7. 项目经历和领域知识无法确认/编辑

AI 解析返回了 `project_exp`（项目经历）和 `domain_knowledge`（领域知识），但 ProfileInput 的确认步骤中完全没有这两个字段的展示和编辑入口。用户无法确认 AI 解析的项目经历是否正确，也无法补充领域知识。

### 8. SSE 解析缺少错误处理

`api.ts:59-66` 中 SSE 数据解析使用 `JSON.parse(line.slice(6))`，没有 try-catch。如果后端返回非 JSON 格式的数据（如错误消息、空行），会直接抛出异常导致整个诊断流程中断，且用户看不到任何有意义的错误提示。

### 9. 小喵对话无上下文记忆

`chat.py:36-41` 每次请求只发送当前一条消息，没有对话历史。用户无法进行连续追问，每次对话都是"失忆"状态。前端 `SalaryCat.tsx` 虽然维护了本地消息列表，但从未将历史消息发送给后端。

### 10. 诊断失败无重试入口

Dashboard 中 SSE 诊断失败时，步骤条会显示 error 状态（红色 ✕），但没有提供任何重试按钮。用户只能刷新页面或重新走 `/input` → `/dashboard` 流程。

---

## 三、🟡 体验问题（影响使用舒适度）

### 11. 页面刷新后状态全丢

Dashboard 直接访问或刷新时，Zustand store 重置，`student` 为 null。虽然 `localStorage` 存了 `student_id`，但 Dashboard 没有尝试用它恢复会话。用户刷新一下就回到"请先填写个人信息"。

### 12. 返回编辑会丢失所有数据

从 Dashboard 点"返回"按钮跳转到 `/input`，但之前填写的数据全部丢失（Zustand store 中 `student` 仍存在但 ProfileInput 不读取它）。用户想修改一个字段必须重新走完整流程。

### 13. 再诊断提示 3 秒消失太快

`ReEvaluatePrompt.tsx:14` 设置 `setTimeout(onDismiss, 3000)`。3 秒对于用户阅读提示并做出"是否重新诊断"的决策来说太短，尤其是重新诊断需要等待较长时间。

### 14. 技能无法删除

用户可以添加新技能（`ProfileInput.tsx:128-135`），但无法删除 AI 解析出的错误技能。只能修改分数，不能移除。

### 15. 版本对比选择器 UX 不佳

`GrowthTab.tsx:57-78` 中两个下拉框选择版本 A/B，但没有防止选择同一版本的校验。如果两个选了相同版本，对比结果全是 0% 变化，容易让用户困惑。

### 16. ExportToolbar 版本号硬编码

`ExportToolbar.tsx:107` 中 `v{diagnosisId ? '2' : '--'}`，版本号写死为 `2`。应该使用 `diagnosisResult.version`。

### 17. 任务完成无证据提交入口

`PathTab.tsx:38` 调用 `completeTask` 时 `evidence` 传空字符串。TaskCard 上也没有输入证据的入口。后端 `settings.py` 定义了 `MAX_EVIDENCE_LENGTH = 500`，说明设计上是希望有证据的，但前端没有实现。

### 18. 成长追踪维度名称未翻译

`GrowthTab.tsx:87` 版本对比表格中维度显示的是原始 key（`tech_skills`、`soft_skills`），而非中文标签（技术能力、软技能）。其他 Tab 都有 `dimLabels` 映射，唯独这里缺失。

### 19. 首页对回访用户不友好

首页只有大标题 + CTA 按钮，没有"快速进入上次诊断"或"查看我的成长进度"的入口。忠实用户每次都要走完整流程。

### 20. 移动端完全不可用

- 首页固定 `flex: '0 0 480px'`，小屏幕文字和图形重叠
- Dashboard 左右布局（160px 侧边栏 + 主内容区）在手机上无法使用
- 小喵对话面板 `width: 340px` 在手机上超出屏幕
- ProfileInput 表单在小屏幕上挤压变形

---

## 四、🔵 设计与视觉问题

### 21. 图表配色与全局设计系统不一致

CSS 变量定义：`--accent-blue: #5b7bb5`，但 ECharts 图表使用 `#5b9cf5`。两套色系相近但不同，雷达图和卡片并排时色差明显。类似问题存在于青色（`#5a9e8f` vs `#2dd4bf`）、紫色（`#8b7ec8` vs `#a78bfa`）。

### 22. 技能标签云颜色单一

`ProfileTab.tsx:128-129` 所有技能标签统一使用蓝色系 `rgba(91,123,181,...)`，没有按四维能力维度着色。失去了与雷达图的视觉关联，也浪费了用颜色传达信息的机会。

### 23. 首页功能标签导航无实际作用

`Home.tsx:134-147` 底部五个功能标签（能力画像、岗位匹配等）的 `href="#features"`，但页面中没有 `id="features"` 的锚点，点击无任何效果。

### 24. Dashboard 左侧导航比例失衡

左侧 Tab 导航宽 160px，但标签文字只有 4-6 字，大量空白。主内容区 `maxWidth: 1100px` 在宽屏下两侧留白过多，在数据密集时又显得局促。

### 25. 缺少深色模式

CSS 变量体系已为深色模式预留了基础，但未实现。对于长时间学习的用户，夜间使用会造成视觉疲劳。

---

## 五、🟢 代码质量与工程问题

### 26. 大量内联样式导致维护困难

几乎所有组件都使用 `style={{}}` 内联样式，导致：
- 相同样式在多个组件中重复（如按钮样式、卡片样式）
- 无法使用 CSS 伪类（:hover、:focus），被迫用 `onMouseEnter/Leave` 模拟
- 同一动画（`pulseGlow`）在 ProgressSteps、TaskCard、PathTimeline 中通过 `<style>` 标签重复注入

### 27. SSE 解析逻辑重复

`api.ts` 中 `startDiagnosis`（第 42-71 行）和 `reEvaluate`（第 89-117 行）的 SSE 读取逻辑几乎完全相同（约 20 行），应提取为公共函数。

### 28. Dashboard 组件过于庞大

`Dashboard.tsx` 有 470+ 行，包含诊断逻辑、再诊断逻辑、Tab 渲染、空状态处理等。已有的 hooks（`useDiagnosis.ts`、`useProgress.ts`、`useReEvaluate.ts`）完全未被使用，Dashboard 内联了所有逻辑。

### 29. useEffect 依赖不完整

`Dashboard.tsx:182-186`：
```typescript
useEffect(() => {
  if (student && !diagnosisResult && !diagnosing) {
    runDiagnosis()
  }
}, [student])  // 缺少 diagnosisResult, diagnosing, runDiagnosis
```
依赖数组不完整，可能导致闭包陷阱或重复触发。

### 30. `any` 类型过多

API 层和 Dashboard 中大量使用 `any`（如 `result: any`、`top5Jobs: any[]`、`project_exp: any[]`），削弱了 TypeScript 的类型安全优势。

### 31. ECharts 未做懒加载

所有图表组件同步导入，ECharts 库体积约 800KB，应使用 `React.lazy` + `Suspense` 按需加载以优化首屏性能。

### 32. 缺少错误边界

如果某个 Tab 组件渲染出错，整个 Dashboard 会崩溃。没有 React Error Boundary 保护。

### 33. Nginx 配置缺少安全头

`nginx.conf` 没有设置 `X-Content-Type-Options`、`X-Frame-Options`、`Content-Security-Policy` 等安全响应头。

### 34. CORS 配置过于宽松

`main.py:18-23` 中 `allow_methods=["*"]`、`allow_headers=["*"]`，生产环境应限制为实际需要的方法和头部。

---

## 六、📊 优先级总览

| 优先级 | 编号 | 问题 | 用户影响 |
|--------|------|------|----------|
| 🔴 P0 | #1 | 图表文字白字白底不可读 | 核心数据完全看不清 |
| 🔴 P0 | #2 | PDF/DOCX 上传实际不可用 | 最常见使用场景失效 |
| 🔴 P0 | #3 | 导出接口前后端不匹配 | 三个导出按钮全部 404 |
| 🔴 P0 | #4 | 任务完成接口参数不匹配 | 标记完成功能完全失效 |
| 🟠 P1 | #5 | 无用户身份系统 | 数据随时可能丢失 |
| 🟠 P1 | #6 | 岗位列表硬编码 | 目标岗位可能不在列表中 |
| 🟠 P1 | #7 | 项目经历/领域知识不可编辑 | 信息确认不完整 |
| 🟠 P1 | #8 | SSE 解析无错误处理 | 诊断异常时无提示 |
| 🟠 P1 | #9 | 小喵对话无上下文 | 无法连续追问 |
| 🟠 P1 | #10 | 诊断失败无重试 | 用户只能刷新重来 |
| 🟡 P2 | #11-14 | 状态丢失/编辑/提示/删除 | 使用舒适度下降 |
| 🟡 P2 | #15-18 | 版本对比/版本号/证据/翻译 | 功能不完善 |
| 🟡 P2 | #19-20 | 回访入口/移动端 | 场景受限 |
| 🔵 P3 | #21-25 | 配色/标签/导航/深色模式 | 视觉体验加分项 |
| 🟢 P4 | #26-34 | 代码质量/性能/安全 | 工程可维护性 |

---

## 七、总结

「职达」在产品定位和设计调性上做得相当出色——温暖的设计语言、可爱的桌宠小喵、完整的诊断闭环概念，这些都是让用户"愿意留下来"的理由。

但从忠实用户的视角，当前最大的问题是**四个 P0 级 bug 让核心功能链断裂**：看不清数据（图表白字）、传不了简历（PDF 乱码）、导不出报告（接口 404）、完不成任务（ID 不匹配）。这四条任何一条都足以让用户认为产品"坏了"。

修复 P0 之后，**用户身份系统**（P1 #5）是下一个最关键的投入——忠实用户最怕的就是积累的成长数据随时消失。

用一句话概括：**产品有灵魂，但骨架的连接点断了**——设计有温度、概念有闭环，但前后端接口对不上、核心交互不可用，需要先把这些"断点"焊上，再谈体验优化。
