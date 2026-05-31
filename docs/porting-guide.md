# 职达 — 移植方案

## 架构抽象层总览

```mermaid
graph TB
    subgraph 前端层
        UI[React 组件] --> Store[Zustand Store]
        Store --> API[API 服务层]
    end
    subgraph 通信层
        API --> REST[REST / SSE]
    end
    subgraph 后端层
        REST --> Router[FastAPI 路由]
        Router --> Service[业务服务]
        Service --> DB[(数据库)]
        Router --> Pipeline[Pipeline 引擎]
        Pipeline --> LLM[LLM 客户端]
    end
```

---

## 数据库移植

### SQLite → PostgreSQL/MySQL

**步骤：**

1. 安装对应驱动：
```bash
# PostgreSQL
pip install asyncpg

# MySQL
pip install aiomysql
```

2. 修改 `backend/config/settings.py` 默认值：
```python
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/zhi_da")
```

3. 修改 `backend/db/database.py` 中的引擎创建：
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(DATABASE_URL, echo=False)
```

4. 迁移数据：
```bash
# 使用 pgloader 或手动导出导入
sqlite3 backend/db/talent_path.db .dump > dump.sql
# 手动转换 SQL 语法差异后导入 PostgreSQL
```

**注意：** ORM 模型使用 SQLAlchemy ORM，SQL 方言差异极小。主要差异在：
- 外键约束配置
- `JSON` 列类型（PostgreSQL 原生支持 JSONB）
- 自增 ID 策略

### 数据库扩展建议（生产环境）

- 为 `student_id`、`diagnosis_id` 添加索引
- `tech_skills` 等 JSON 字段考虑拆分为关联表以支持按技能名查询
- 添加连接池配置（`pool_size=20, max_overflow=10`）

---

## LLM 提供商移植

### OpenAI → 国内大模型（DeepSeek / 通义千问 / 智谱）

因 `core/harness/llm.py` 使用 OpenAI SDK 统一接口，所有兼容 OpenAI API 格式的提供商只需修改环境变量：

```env
# DeepSeek
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 通义千问
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus

# 智谱 GLM
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
```

### OpenAI → 其他非 OpenAI 格式（Claude / Gemini）

需在 `core/harness/llm.py` 中新增实现类：

```python
class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def complete(self, messages: list[dict]) -> LLMResponse:
        # Anthropic 使用 system 参数而非 system role
        system_msg = ""
        user_msgs = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                user_msgs.append(m)
        resp = await self.client.messages.create(
            model=self.model,
            system=system_msg,
            messages=user_msgs,
            max_tokens=4096,
        )
        return LLMResponse(content=resp.content[0].text)
```

然后在 `get_llm_client()` 工厂函数中添加分支即可。

---

## 前端框架移植

### React + Vite → Next.js

| 当前 | 替换为 | 说明 |
|------|--------|------|
| React Router v6 | Next.js App Router | 文件系统路由自动映射 |
| Vite 构建 | Next.js 内置 Webpack/Turbopack | 构建配置变更 |
| `index.html` | `app/layout.tsx` | 根布局 |
| Zustand Store | 保持不变 | Zustand 无框架依赖 |
| CSS 变量 | 保持不变 | CSS 变量浏览器原生支持 |

### React + Vite → Vue 3

| 当前 | 替换为 | 说明 |
|------|--------|------|
| React 组件 | Vue SFC | JSX → `<template>` 语法 |
| Zustand | Pinia | Vue 生态状态管理 |
| React Router | Vue Router | API 差异较大 |
| `echarts-for-react` | `vue-echarts` | ECharts Vue 封装 |
| `onMouseEnter` 等 | `@mouseenter` | 事件语法不同 |

---

## 前端构建工具移植

### Vite → Webpack

```bash
npm install --save-dev webpack webpack-cli webpack-dev-server \
  html-webpack-plugin ts-loader css-loader style-loader
```

创建 `webpack.config.js`：
```javascript
module.exports = {
  entry: './src/main.tsx',
  resolve: { extensions: ['.ts', '.tsx', '.js'] },
  module: { rules: [
    { test: /\.tsx?$/, use: 'ts-loader' },
    { test: /\.css$/, use: ['style-loader', 'css-loader'] },
  ]},
  plugins: [new HtmlWebpackPlugin({ template: 'index.html' })],
  devServer: { port: 5173, proxy: { '/api': 'http://localhost:8000' } },
}
```

---

## 容器化平台移植

### Docker Compose → Kubernetes

创建 `k8s/` 目录：

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zhi-da-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: zhi-da-backend
  template:
    metadata:
      labels:
        app: zhi-da-backend
    spec:
      containers:
      - name: backend
        image: ccnnd/zhi-da-backend:latest
        env:
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secret
              key: api-key
        - name: DATABASE_URL
          value: "postgresql+asyncpg://user:pass@postgres-svc/zhi_da"
```

---

## 日志与监控

当前无生产级日志/监控。建议移植时加入：

```python
# backend/config/settings.py 新增
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zhi-da")

# 在 main.py 中添加请求中间件
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{response.status_code}")
    return response
```

推荐的监控方案：
- **日志**：`structlog` + ELK Stack
- **APM**：Sentry / DataDog
- **健康检查**：已内置 `/api/health` 端点

---

## 性能优化建议（生产环境）

| 优化项 | 当前状态 | 目标方案 |
|--------|---------|---------|
| 数据库连接池 | 无配置 | `pool_size=20, max_overflow=10` |
| 静态资源 CDN | 无 | Nginx `try_files` + CDN |
| ECharts 懒加载 | 全量导入 | `React.lazy` + 按需加载 |
| SSE 限流 | 无 | 单用户最多 1 路 SSE 连接 |
| LLM 并发 | 5 步顺序 | `asyncio.gather` 并行非依赖步骤 |
| API 限流 | 无 | `slowapi` + Redis |
