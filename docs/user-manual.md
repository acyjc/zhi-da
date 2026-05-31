# 职达 — 使用手册

## 系统要求

| 组件 | 最低版本 |
|------|---------|
| 操作系统 | Windows 10 / macOS 11+ / Linux |
| Python | 3.11+ |
| Node.js | 18+ |
| 浏览器 | Chrome 90+ / Edge 90+ / Safari 15+ |

---

## 安装与启动

### 方式一：本地开发

**后端：**

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY（可选，不填则 Mock 模式）
python main.py
```

启动后访问 `http://localhost:8000/docs` 可查看 Swagger API 文档。

**前端：**

```bash
cd frontend
npm install
npm run dev
```

启动后访问 `http://localhost:5173`。

### 方式二：Docker 部署

```bash
docker-compose up --build
# 前端 → http://localhost
# 后端 → http://localhost:8000
```

---

## 功能详解

### 1. 首页（Home）

- 展示产品标题"你的职业成长伙伴"和简要介绍
- 点击 **"上传简历，开始诊断"** 或 **"开始诊断"** 进入信息输入页
- 如果之前已有诊断记录，会显示 **"继续上次诊断"** 快捷入口

### 2. 信息输入（ProfileInput）

**步骤 1：上传简历**
- 拖拽 PDF/DOCX/TXT 文件到虚线框，或点击选择
- 也可以在下方文本框中直接粘贴简历内容
- 点击 **"AI 解析简历"**，后端调用 LLM 自动提取姓名、技能、项目经历等
- 如果没有简历，可以点击 **"跳过解析，手动填写"**

**步骤 2：确认信息**
- 检查 AI 解析结果：姓名、年级、专业、目标岗位
- 技能确认：每个技能的评分可下拉修改，点击 ✕ 可删除，底部可添加新技能
- 软技能：沟通表达/团队协作/学习能力，可修改评分
- 项目经历：查看和编辑 AI 解析出的项目名称、角色、描述
- 领域知识：查看和编辑解析出的领域知识评分
- 点击 **"确认并开始诊断"** 提交

### 3. 诊断看板（Dashboard）

提交后进入看板，AI 自动开始 SSE 流式诊断（5 步），左侧有 6 个 Tab：

#### 3.1 能力画像（Profile）
- ECharts 雷达图展示四维能力
- 2×2 卡片显示各维度具体分值
- 再诊断后显示 +N/-N 变化幅度
- 技能标签云按维度着色（蓝/青/紫/琥珀）

#### 3.2 岗位匹配（Match）
- 半圆仪表盘显示综合匹配度百分比
- vs 上次诊断的变化箭头
- 四维匹配度百分比卡片
- TOP5 岗位排行（带进度条和匹配度）
- 差距分析横向柱状图（当前值 vs 要求值）

#### 3.3 成长路径（Path）
- 横向阶段时间线
- 左侧阶段导航栏（含周数和任务数）
- 右侧任务卡片列表：任务名称、描述、资源链接、达标标准
- 点击 **"标记完成"** 可以填写完成证据，提交后自动更新技能值

#### 3.4 职业建议（Advice）
- 带左侧彩色竖线的建议文本
- 推荐方向标签
- AI 推理依据面板

#### 3.5 就业推荐（Recommend）
- 5 张岗位推荐卡：圆形 SVG 进度环 + 排名徽章 + 岗位名称 + 匹配度评价

#### 3.6 成长追踪（Growth）
- ECharts 折线图显示各维度随时间变化趋势
- 版本对比：选择两个版本 A/B，查看维度分值和变化百分比
- 诊断历史时间线：V1/V2/V3...每版本显示日期、触发事件、匹配度

### 4. 导出功能

底部工具栏三个按钮：
- **导出 JSON**：能力画像的完整 JSON 文件
- **导出 Excel**：能力画像工作表 + TOP5 岗位工作表
- **导出 PDF**：成长路径规划报告

### 5. 重新诊断

顶部导航栏右侧 **"重新诊断"** 按钮，或在标记任务完成后底部弹出的提示条中点击 **"立即重新诊断"**。再诊断会基于最新的能力值重新生成所有分析结果。

### 6. 职达小喵（SalaryCat）

右下角橙色猫猫图标：
- 点击展开对话面板
- 首次展开显示 4 个快捷问题按钮
- 输入问题后回车或点发送按钮
- 小喵仅回答职业成长、技能学习、面试求职领域的问题
- 支持多轮上下文记忆

---

## 配置文件说明

| 文件 | 位置 | 内容 |
|------|------|------|
| `.env` | `backend/.env` | LLM 密钥、模型、CORS 策略 |
| `settings.py` | `backend/config/settings.py` | 默认配置（数据库 URL、上传限制） |
| `index.css` | `frontend/src/index.css` | 全局 CSS 变量（主题色、字体、圆角） |
| `nginx.conf` | `frontend/nginx.conf` | Nginx 反向代理配置 |
| `docker-compose.yml` | 根目录 | 前后端容器编排 |

---

## 故障排除

### 前端构建失败

```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### 后端启动失败

```bash
cd backend
# 检查 Python 版本 ≥ 3.11
python --version

# 重装依赖
pip install -r requirements.txt

# 直接测试是否可运行
python -c "from main import app; print('OK')"
```

### LLM 调用失败

1. 确认 `backend/.env` 中 `LLM_API_KEY` 已正确设置
2. 确认 `LLM_BASE_URL` 可访问（某些 API 需要代理）
3. 不设置 API Key 则自动降级为 Mock 模式

### 数据库问题

删除 `backend/db/talent_path.db` 后重启后端即可自动重建：

```bash
rm backend/db/talent_path.db
cd backend && python main.py
```

### 简历解析失败

- 确认文件格式为 PDF/DOCX/TXT
- 文件大小不超过 10MB
- PDF 文件确保不是纯扫描版（需要可提取文字）
- 解析失败后可手动填写信息，不影响后续诊断

---

## 测试

```bash
# 后端 14 个测试
cd backend && python -m pytest tests/ -v

# 前端 6 个测试
cd frontend && npm test
```

---

## API 接口速查

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/students` | 创建学生 |
| GET/PUT | `/api/students/{id}` | 查询/更新学生 |
| PUT | `/api/students/{id}/skills` | 手动更新技能 |
| GET | `/api/jobs` | 岗位列表 |
| POST | `/api/diagnosis/full` | SSE 流式初诊 |
| POST | `/api/diagnosis/re-evaluate` | SSE 流式再诊 |
| GET | `/api/diagnosis/history/{id}` | 诊断历史 |
| GET | `/api/diagnosis/{id}` | 单条诊断详情 |
| POST | `/api/progress/task-complete` | 标记任务完成 |
| GET | `/api/progress/{student_id}` | 任务进度列表 |
| POST | `/api/resume/parse` | 文本简历解析 |
| POST | `/api/resume/upload` | 文件简历上传解析 |
| POST | `/api/chat` | 小喵对话 |
| GET | `/api/export/profile/{id}` | JSON 导出 |
| GET | `/api/export/profile/{id}/excel` | Excel 导出 |
| GET | `/api/export/path/{id}` | PDF 导出 |
| GET | `/api/health` | 健康检查 |
