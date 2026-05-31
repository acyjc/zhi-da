# 🔍 「职达」功能逻辑审查报告（第二轮）

> 审查范围：前端全部页面/组件/API 层 + 后端路由/模型，聚焦功能逻辑正确性和数据流完整性
> 审查时间：2026-05-31

---

## 已修复确认（21/21）✅

| 上次问题 | 当前状态 | 修复方式 |
|----------|---------|---------|
| 图表白字白底不可读 | ✅ | tooltip/detail 颜色改为 `#1d1d1f` |
| PDF/DOCX 上传乱码 | ✅ | 新增 `uploadResumeFile` + 后端 `/upload` 端点 + PyPDF2/docx 解析 |
| 导出接口 404 | ✅ | `exportUrls` 映射与后端路径一致 |
| 岗位硬编码 | ✅ | `listJobs()` 动态加载岗位列表 |
| 项目经历不可编辑 | ✅ | 确认步骤新增项目经历展示和编辑区块 |
| 领域知识不可编辑 | ✅ | 确认步骤新增领域知识展示和编辑区块 |
| SSE 解析无错误处理 | ✅ | `readSSE` 提取为公共函数 + try-catch 包裹 JSON.parse |
| 小喵无对话上下文 | ✅ | 前端发送完整 `messages` 数组 + 后端接收 `list[ChatMessage]` |
| 诊断失败无重试 | ✅ | 新增 `diagnosisError` 状态 + "重新诊断"重试按钮 |
| 技能无法删除 | ✅ | 每个技能旁新增 ✕ 删除按钮 |
| ExportToolbar 版本号硬编码 | ✅ | `version` prop 传入，显示实际版本号 |
| 版本对比可选同版本 | ✅ | 同版本时显示提示"请选择不同的版本进行对比" |
| 成长追踪维度未翻译 | ✅ | GrowthTab 新增 `dimLabels` 映射 |
| 再诊断提示 3 秒消失 | ✅ | 改为 15 秒 |
| 首页无回访入口 | ✅ | `hasExistingSession` + "继续上次诊断"按钮 |
| 页面刷新丢失状态 | ✅ | `hydrateFromStorage` + `getStudent` 从后端恢复 |
| 返回编辑丢失数据 | ✅ | `existingStudent` 预填充 + 直接进入 review 步骤 |
| 任务完成无证据 | ✅ | TaskCard 新增 evidence 输入框 |
| 技能标签云颜色单一 | ✅ | 按维度着色（四种颜色对应四个维度） |
| 图表配色不一致 | ✅ | CHART_COLORS 改为与 CSS 变量一致的色值 |
| 首页功能标签无作用 | ✅ | `href` 改为 `/input` |
| 小喵面板移动端溢出 | ✅ | `width: min(340px, calc(100vw - 48px))` |

---

## 仍存在的功能逻辑问题

---

### 🔴 P0 —— 严重逻辑缺陷

#### 1. 任务完成仍不可用：task_id 传的是名称而非数据库 ID

**问题链路**：

- [PathTab.tsx:101] 中 `const taskId = task.name`（如 "学习Python基础"）
- [PathTab.tsx:38-42] 调用 `completeTask({ task_id: taskName, evidence })`
- 后端 [progress.py:16] 用 `TaskORM.id` 查找：`select(TaskORM).where(TaskORM.id == req.task_id)`
- `TaskORM.id` 是 8 位 UUID（如 `a3f2b9c1`），用任务名称去查 UUID **永远匹配不到**

**更深层的问题**：诊断结果 `growth_path.phases[].tasks[]` 中只包含 `name/description/resources/criteria`，根本没有后端 `TaskProgress` 表的 `id` 字段。前端压根拿不到真正的数据库 task_id。

**影响**：成长路径中"标记完成"功能完全不可用。用户点击后后端返回 `{"success": false, "error": "Task not found"}`，但错误被 [PathTab.tsx:45] 的 `catch {}` 静默吞掉了。

**修复方向**：
- 后端在诊断结果中为每个 task 返回 `id` 字段
- 或后端 `completeTask` 改为按 `student_id + task_name` 查找

---

#### 2. Dashboard 刷新后自动触发重复诊断

**问题链路**：

[Dashboard.tsx:202-213] 会话恢复逻辑：
```typescript
hydrateFromStorage()  // 从 localStorage 恢复 student（不含 diagnosisResult）
getStudent(storedId).then(data => setStudent(data))  // 再次设置 student
```

[Dashboard.tsx:187-191] 自动诊断触发：
```typescript
useEffect(() => {
  if (student && !diagnosisResult && !diagnosing) {
    runDiagnosis()  // student 有值，diagnosisResult 为 null → 触发诊断！
  }
}, [student, diagnosisResult, diagnosing, runDiagnosis])
```

**触发流程**：用户刷新 → `hydrateFromStorage` 设置 student → `diagnosisResult` 仍为 null → 自动触发一次完整诊断。

**影响**：
- 用户刷新页面会重新执行一次完整 LLM 诊断（浪费 API 调用）
- 旧的诊断结果被覆盖，历史版本记录被污染
- 用户看到的是全新诊断而非上次的结果

**修复方向**：恢复时同步加载最近的诊断结果（`GET /api/diagnosis/history/{student_id}` 取第一条），存入 `diagnosisResult`。

---

#### 3. ProfileInput 返回编辑时创建新学生，历史数据断裂

**问题链路**：

[ProfileInput.tsx:76-92] 从 Dashboard 返回时预填充了 `existingStudent` 的数据，但 [ProfileInput.tsx:160-179] 提交时始终调用 `createStudent`：

```typescript
const student = await createStudent({
  name, grade: parsed.grade, major: parsed.major, ...
})
setStudent(student)
localStorage.setItem('student_id', student.id)  // 覆盖了旧 ID
setDiagnosisResult(null)
```

**影响**：
- 每次编辑都创建一个全新的学生记录
- 旧学生的诊断历史、任务进度、成长记录全部与新学生断开
- `localStorage` 中的 `student_id` 被覆盖，用户再也找不回旧数据

**修复方向**：
- 如果 `existingStudent` 存在，调用更新接口（PUT）而非创建接口（POST）
- 后端需补充 `PUT /api/students/{student_id}` 通用更新端点

---

### 🟠 P1 —— 中等逻辑问题

#### 4. buildProfile 的 fallback 分支丢失了技能子项

[Dashboard.tsx:34-37]：
```typescript
const makeDim = (key: string): AbilityDimension => {
  const score = result?.dimension_scores?.[key] ?? 0
  return { weight: score, sub_items: [] }  // sub_items 始终为空！
}
```

当后端返回扁平的 `dimension_scores: { tech_skills: 0.72, ... }` 格式时（而非嵌套的 `ability_profile`），`sub_items` 始终为空数组。

[ProfileTab.tsx:33] 从 `sub_items` 取数据构建技能标签云，因此**标签云永远显示为空**。

**影响**：如果后端 pipeline 没有返回 `ability_profile.sub_items` 结构，用户的能力画像 Tab 中看不到技能标签云。

**修复方向**：`buildProfile` 需要从源数据（`student.tech_skills`、`student.soft_skills` 等）构建 `sub_items`，而非依赖诊断结果。

---

#### 5. GrowthTrend X 轴日期解析错误——显示 NaN/NaN

[GrowthTrend.tsx:27-29]：
```typescript
const dates = history.map((h) => {
  const d = new Date(h.date)  // h.date = "V1", "V2", "V3"
  return `${d.getMonth() + 1}/${d.getDate()}`
})
```

[GrowthTab.tsx:44] 传入 `date: 'V${d.version}'`，`new Date("V1")` 返回 `Invalid Date`，`getMonth()` 返回 `NaN`。X 轴会显示 `NaN/NaN`。

**影响**：成长趋势折线图的 X 轴刻度全部显示 `NaN/NaN`，图表无法正常阅读。

**修复方向**：GrowthTrend 应直接使用 `h.date` 原始字符串作为 X 轴标签，不需要解析为 Date 对象。

---

#### 6. completeTask 失败时静默吞错，无用户反馈

[PathTab.tsx:44-46]：
```typescript
try {
  await completeTask({ ... })
  setCompletedTasks(prev => new Set([...prev, taskName]))
  onTaskComplete(taskName)
} catch {
  // 空的 catch 块 —— 错误被完全吞掉
}
```

**影响**：任务完成失败时无任何提示。用户点击"标记完成"后按钮恢复正常，但任务并未真正完成。结合问题 #1，用户每次标记完成都会失败且完全不知情。

---

#### 7. 再诊断后 dimension_changes 始终为空

[Dashboard.tsx:110] 中 `dimension_changes: result.dimension_changes ?? {}`，但后端 [diagnosis.py:50] 保存诊断时 `dimension_changes={}` 始终为空对象。

**影响**：后端没有计算两次诊断之间的维度差异，因此 ProfileTab 中四维分值旁边的 `+N/-N` 变化标记永远不会出现。再诊断后用户看不到自己哪方面进步了。

---

#### 8. 导出只取最新版本，无法导出历史诊断

[ExportToolbar.tsx:28-32] 导出 URL 只含 `studentId`，不含 `diagnosisId`。后端 [export.py] 始终取该学生的 `limit(1)` 最新诊断。

**影响**：用户只能导出最新版本的诊断报告。如果想对比或导出之前某次诊断的报告，无法实现。

---

### 🟡 P2 —— 轻微逻辑问题

#### 9. 小喵前端发送全量历史消息

[SalaryCat.tsx:42-43] 把完整的 `newMessages` 数组（可能几十条）发给后端，但后端 [chat.py:43] 只取 `[-10:]`。

**影响**：无功能问题，但浪费带宽。建议前端也限制为最近 10 条。

---

#### 10. hydrateFromStorage 与 getStudent 存在竞态

[Dashboard.tsx:203-213] 中 `hydrateFromStorage()`（同步）和 `getStudent()`（异步）都可能设置 student。localStorage 数据可能已过期（如后端技能已更新），导致先用旧数据渲染再用新数据覆盖，界面闪烁。

---

#### 11. 文件上传覆盖粘贴文本无提示

[ProfileInput.tsx:119-120] 中如果用户同时上传了文件和粘贴了文本，`handleParse` 优先使用文件。用户粘贴的文本被静默忽略，可能困惑。

---

#### 12. 预填充后"重新上传"覆盖已编辑数据

[ProfileInput.tsx:77-91] 中若 `existingStudent` 存在则直接跳到 review。但 review 步骤中的"← 重新上传"按钮会 `setStep('upload')`，此时用户可重新上传简历，解析结果会覆盖之前预填充的所有数据，包括用户手动修正的字段。

---

#### 13. GrowthTab 版本对比方向语义不清

[GrowthTab.tsx:38] 中 `change = valA - valB`，但 A 和 B 哪个是旧版哪个是新版无约束。用户可能选 A=V2、B=V1（变化 = +10%，进步）或 A=V1、B=V2（变化 = -10%，退步），结果完全取决于选择顺序，容易混淆。

---

## 📊 优先级总览

| 优先级 | 编号 | 问题 | 用户影响 |
|--------|------|------|----------|
| 🔴 P0 | #1 | 任务完成 task_id 类型不匹配 | 标记完成功能仍完全不可用 |
| 🔴 P0 | #2 | 刷新后自动重新诊断 | 浪费 LLM API + 历史上下文丢失 |
| 🔴 P0 | #3 | 返回编辑创建新学生 | 诊断历史/任务进度全部断裂 |
| 🟠 P1 | #4 | buildProfile 丢失 sub_items | 技能标签云可能为空 |
| 🟠 P1 | #5 | GrowthTrend X 轴 NaN/NaN | 趋势图 X 轴完全不可读 |
| 🟠 P1 | #6 | completeTask 静默吞错 | 用户误以为操作成功 |
| 🟠 P1 | #7 | dimension_changes 始终为空 | 再诊断变化标记永远不显示 |
| 🟠 P1 | #8 | 导出不区分版本 | 只能导出最新版报告 |
| 🟡 P2 | #9 | 对话历史发全量 | 轻微带宽浪费 |
| 🟡 P2 | #10 | hydrate/getStudent 竞态 | 界面可能闪烁 |
| 🟡 P2 | #11 | 文件覆盖文本无提示 | 用户可能困惑 |
| 🟡 P2 | #12 | 重新上传覆盖编辑 | 操作性数据丢失 |
| 🟡 P2 | #13 | 版本对比方向不清 | 对比结果可能反直觉 |

---

## 总结

第一轮的 21 个问题已全部修复，代码质量飞跃式提升。但第二轮深入功能逻辑层后，发现了**三个新的 P0 级数据断裂问题**，都围绕相同的根因：**数据在关键流转节点上没有正确传递或持久化**——

1. 任务名称 vs 数据库 ID —— 前后端约定不一致
2. 诊断结果没有被缓存/恢复 —— localStorage 只存了 student 没存 diagnosis
3. 编辑走创建而非更新 —— 没有区分新建和修改场景

修复完这三个 P0 后，产品的核心闭环才能真正跑通：**输入信息 → 诊断 → 查看结果 → 完成任务 → 再诊断 → 对比成长**。
