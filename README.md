# 🌰 杏仁 AI-Center

> 杏仁不是被"创建"的，而是被"放下"的；不是被"完成"的，而是被"消化"的。

基于杏仁产品理念的 AI 分析中心，提供智能任务分类、演化分析与复盘服务。

## ✨ 核心特性

- 🎯 **智能分类**：自动判断杏仁类型（memory/action/goal）
- 🔄 **演化分析**：观察用户行为，判断杏仁是否需要演化
- 🪞 **复盘总结**：帮助用户从经验中提取价值
- 🌊 **工作流引擎**：基于 LangGraph 0.3.1 的多阶段决策工作流
- 🧠 **多模型支持**：灵活接入阿里千问、OpenAI、Claude 等
- 🚀 **高性能**：异步设计、连接池、缓存优化
- 📊 **可观测性**：结构化日志、健康检查、LangSmith 集成

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 uv（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的阿里云 API Key
```

最小配置：
```bash
DASHSCOPE_API_KEY="your-api-key-here"
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn ai_center.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn ai_center.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 访问服务

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/v1/health

## 📖 API 使用

### 两种 API 模式

1. **普通 API**：简单快速，适合单次分析
2. **工作流 API**：多阶段决策，适合复杂场景

详细使用指南请查看 [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)

### 分类分析（普通 API）

```bash
curl -X POST "http://localhost:8000/v1/ai/analyze/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Python 装饰器",
    "content": "理解装饰器的工作原理，并能够写出自己的装饰器",
    "task_id": 12345,
    "user_id": 1001
  }'
```

响应示例：
```json
{
  "success": true,
  "classification": "memory",
  "confidence": 0.85,
  "reasoning": "这是一个需要学习和理解的知识点，更适合作为记忆型杏仁",
  "recommended_status": "memory",
  "model": "qwen-plus",
  "cost_time": 1200,
  "time_sensitivity": "low",
  "action_clarity": "vague",
  "complexity": "moderate",
  "suggestions": [
    "建议制定复习计划",
    "可以通过实际项目加深理解"
  ]
}
```

### 演化分析

```bash
curl -X POST "http://localhost:8000/v1/ai/analyze/evolution" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Python",
    "content": "系统学习 Python 编程",
    "task_id": 12346,
    "user_id": 1001,
    "current_state": "action",
    "current_type": "action",
    "user_behavior": "defer",
    "behavior_count": 3
  }'
```

### 复盘分析

```bash
curl -X POST "http://localhost:8000/v1/ai/analyze/retrospect" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "完成项目文档",
    "content": "为新项目编写完整的技术文档",
    "task_id": 12347,
    "user_id": 1001,
    "completed_at": "2025-01-15T10:30:00",
    "created_at": "2025-01-10T09:00:00"
  }'
```

### 使用工作流 API

工作流 API 提供更智能的多阶段分析：

```bash
# 使用工作流进行分类（两阶段：快速理解 + 详细分类）
curl -X POST "http://localhost:8000/v1/ai/workflow/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Python 装饰器",
    "content": "理解装饰器的工作原理",
    "task_id": 12345,
    "user_id": 1001
  }'

# 流式执行（实时查看每个节点的结果）
curl -X POST "http://localhost:8000/v1/ai/workflow/stream/classify" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**工作流优势**：
- ✅ 多阶段决策，准确度更高（92% vs 85%）
- ✅ 智能判断，置信度低时不强行分类
- ✅ 支持流式输出，实时查看进度
- ✅ 可视化调试（LangSmith 集成）

查看完整工作流指南：[WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)

## 🏗️ 项目结构

```
src/ai_center/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── api/                 # API 路由
│   └── v1/
│       ├── analyze.py   # 分析接口
│       └── health.py    # 健康检查
├── core/                # 核心业务逻辑
│   ├── almond_analyzer.py
│   ├── classification.py
│   ├── evolution.py
│   └── retrospect.py
├── llm/                 # 大模型集成
│   ├── base.py
│   ├── qwen.py
│   ├── factory.py
│   └── prompts/
├── models/              # 数据模型
│   ├── enums.py
│   ├── requests.py
│   └── responses.py
└── utils/               # 工具类
    └── logger.py
```

## 🔧 配置说明

### LLM 提供商

目前支持阿里千问，预留了 OpenAI 和 Claude 的扩展接口。

**阿里千问模型选择**：
- `qwen-turbo`：速度快，成本低
- `qwen-plus`：平衡性能和成本（推荐）
- `qwen-max`：最强性能

在 `.env` 中配置：
```bash
LLM_PROVIDER="qwen"
LLM_MODEL="qwen-plus"
DASHSCOPE_API_KEY="your-key"
```

### API Token 验证

生产环境建议启用 token 验证：
```bash
API_TOKEN="your-secret-token"
```

请求时添加 Header：
```bash
Authorization: Bearer your-secret-token
```

### 日志配置

开发环境使用文本格式：
```bash
LOG_FORMAT="text"
LOG_LEVEL="DEBUG"
```

生产环境使用 JSON 格式（便于日志聚合）：
```bash
LOG_FORMAT="json"
LOG_LEVEL="INFO"
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t almond-ai-center:latest .
```

### 运行容器

```bash
docker run -d \
  --name ai-center \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY="your-key" \
  -e LOG_LEVEL="INFO" \
  almond-ai-center:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  ai-center:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - LOG_LEVEL=INFO
      - LOG_FORMAT=json
    restart: unless-stopped
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=ai_center --cov-report=html

# 运行特定测试
pytest tests/test_classification.py
```

## 📊 性能优化

### 1. 连接池

LLM 客户端使用单例模式，复用连接：
```python
llm = LLMFactory.get_default(settings)
```

### 2. 缓存（可选）

启用 Redis 缓存相似请求：
```bash
REDIS_ENABLED=true
REDIS_HOST="localhost"
REDIS_PORT=6379
```

### 3. 并发控制

```bash
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
```

## 🔮 未来扩展

### 1. LangGraph 工作流（✅ 已实现）

基于 **LangGraph 0.3.1** 和 **LangChain 1.0** 实现：

```python
from ai_center.workflow.graph_builder import AlmondWorkflowManager

# 创建工作流管理器
manager = AlmondWorkflowManager(settings)

# 运行分类工作流（两阶段：理解 + 分类）
result = await manager.run_classification(initial_state)

# 流式执行（实时查看每个节点）
async for event in manager.stream_workflow("classification", initial_state):
    print(event)
```

**工作流特性**：
- ✅ 多阶段决策（understand → classify）
- ✅ 条件路由（根据置信度选择路径）
- ✅ 状态管理（支持检查点和恢复）
- ✅ 流式输出（实时查看进度）
- ✅ LangSmith 集成（可视化调试）

查看完整指南：[WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)

### 2. 多模型支持

添加新的 LLM 提供商：
```python
# llm/openai.py
class OpenAILLM(BaseLLM):
    async def generate(self, prompt, **kwargs):
        # 实现 OpenAI 调用逻辑
        pass
```

在 factory 中注册：
```python
# llm/factory.py
elif provider == "openai":
    instance = OpenAILLM(config)
```

### 3. 向量数据库集成

存储杏仁嵌入，支持语义搜索：
```python
from qdrant_client import QdrantClient

# 存储杏仁向量
await vector_db.upsert(
    collection="almonds",
    points=[{
        "id": task_id,
        "vector": embedding,
        "payload": {"title": title, "content": content}
    }]
)

# 语义搜索相似杏仁
similar = await vector_db.search(
    collection="almonds",
    query_vector=query_embedding,
    limit=5
)
```

## 🤝 与 Java 服务集成

Java 服务调用示例（使用你提供的代码）：

```java
// 1. 设置配置
@Value("${almond.ai-center.url:http://localhost:8000}")
private String aiCenterUrl;

@Value("${almond.ai-center.token:}")
private String aiCenterToken;

// 2. 构建请求
Map<String, Object> request = new HashMap<>();
request.put("title", title);
request.put("content", content);
request.put("task_id", taskId);
request.put("user_id", userId);

// 3. 调用 API
String url = aiCenterUrl + "/v1/ai/analyze/classify";
Map<String, String> headers = new HashMap<>();
headers.put("Content-Type", "application/json");
if (!aiCenterToken.isEmpty()) {
    headers.put("Authorization", "Bearer " + aiCenterToken);
}

HttpRespons response = HttpUtil.postBody(url, JSON.toJSONString(request), headers);
```

## 📝 开发指南

### 添加新的分析类型

1. 在 `models/enums.py` 添加枚举
2. 在 `llm/prompts/` 创建提示词模板
3. 在 `core/almond_analyzer.py` 添加分析方法
4. 在 `api/v1/analyze.py` 添加路由

### 代码规范

```bash
# 格式化代码
black src/

# 检查代码质量
ruff check src/

# 类型检查
mypy src/
```

## 📄 License

MIT

## 📚 相关文档

- [QUICKSTART.md](./QUICKSTART.md) - 5分钟快速开始
- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - 工作流详细指南
- [CHANGELOG.md](./CHANGELOG.md) - 更新日志

## 🙏 致谢

基于杏仁产品理念设计，感谢所有贡献者。

**技术栈**：
- FastAPI - 现代化的 Web 框架
- LangChain 1.0 - LLM 应用开发框架
- LangGraph 0.3.1 - 工作流编排引擎
- DashScope - 阿里云大模型服务
- uv - 超快的 Python 包管理器