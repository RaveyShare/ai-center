# ⚡ 5分钟快速开始

## 前置要求

- Python 3.11+
- 阿里云 DashScope API Key（[申请地址](https://dashscope.console.aliyun.com/)）

## 🚀 快速部署

### 方式一：使用启动脚本（推荐）

```bash
# 1. 克隆项目
git clone <your-repo>
cd almond-ai-center

# 2. 给脚本执行权限
chmod +x scripts/start.sh

# 3. 运行启动脚本（会自动创建 .env 并提示配置）
./scripts/start.sh
```

第一次运行会提示你配置 API Key：

```bash
# 编辑 .env 文件
vim .env

# 填入你的 API Key
DASHSCOPE_API_KEY="sk-xxxxxxxxxxxx"
```

然后再次运行：

```bash
./scripts/start.sh        # 开发模式
./scripts/start.sh prod   # 生产模式
```

### 方式二：手动安装

```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 创建虚拟环境
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 安装依赖
uv pip install -e ".[dev]"

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 5. 启动服务
uvicorn ai_center.main:app --reload
```

### 方式三：使用 Docker

```bash
# 1. 构建镜像
docker build -t almond-ai-center .

# 2. 运行容器
docker run -d \
  --name ai-center \
  -p 8000:8000 \
  -e DASHSCOPE_API_KEY="your-key" \
  almond-ai-center
```

## 🎯 验证安装

访问 http://localhost:8000/docs 查看 API 文档。

### 测试分类 API

```bash
curl -X POST "http://localhost:8000/v1/ai/analyze/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Python",
    "content": "系统学习 Python 编程"
  }'
```

### 测试工作流 API

```bash
curl -X POST "http://localhost:8000/v1/ai/workflow/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "学习 Python",
    "content": "系统学习 Python 编程"
  }'
```

## 🔧 配置选项

### 基础配置（最小）

```bash
# .env
DASHSCOPE_API_KEY="sk-xxxxxxxxxxxx"
```

### 完整配置

```bash
# 应用配置
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# LLM 配置
LLM_PROVIDER=qwen
LLM_MODEL=qwen-plus      # qwen-turbo/qwen-plus/qwen-max
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000

# API 安全
API_TOKEN=your-secret    # 可选，用于 token 验证

# 性能配置
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
```

## 📊 性能调优

### 选择合适的模型

| 模型 | 速度 | 成本 | 质量 | 适用场景 |
|------|------|------|------|---------|
| qwen-turbo | ⚡⚡⚡ | 💰 | ⭐⭐⭐ | 快速分类 |
| qwen-plus | ⚡⚡ | 💰💰 | ⭐⭐⭐⭐ | 平衡（推荐） |
| qwen-max | ⚡ | 💰💰💰 | ⭐⭐⭐⭐⭐ | 复杂分析 |

```bash
# .env
LLM_MODEL=qwen-plus  # 推荐使用
```

### 生产环境优化

```bash
# 使用多 worker
uvicorn ai_center.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4          # CPU 核心数
  --log-level info

# 或使用 Gunicorn
gunicorn ai_center.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

## 🐛 常见问题

### 1. 导入错误

```bash
# 确保使用可编辑安装
uv pip install -e .
```

### 2. API Key 错误

```bash
# 检查 .env 文件
cat .env | grep DASHSCOPE_API_KEY

# 确保没有多余空格或引号
DASHSCOPE_API_KEY=sk-xxxx  # ✅ 正确
DASHSCOPE_API_KEY="sk-xxxx"  # ✅ 正确
DASHSCOPE_API_KEY= sk-xxxx   # ❌ 错误（有空格）
```

### 3. 端口被占用

```bash
# 使用其他端口
uvicorn ai_center.main:app --port 8001
```

### 4. LangGraph 版本问题

```bash
# 确保安装了正确版本
uv pip list | grep langgraph
# 应该显示 langgraph>=0.3.1

# 如果版本不对，重新安装
uv pip install --upgrade langgraph
```

## 🎓 下一步

- 📖 阅读 [README.md](./README.md) 了解完整功能
- 🌊 查看 [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) 学习工作流
- 💻 运行 [examples/workflow_demo.py](./examples/workflow_demo.py) 查看示例
- 🧪 运行测试：`pytest tests/`

## 💡 快速示例

### Python 调用

```python
import asyncio
from ai_center import AlmondAnalyzer, Settings

async def main():
    settings = Settings(dashscope_api_key="your-key")
    analyzer = AlmondAnalyzer(settings)
    
    result = await analyzer.classify(
        title="学习 Python",
        content="系统学习 Python 编程"
    )
    
    print(f"分类: {result.classification}")
    print(f"置信度: {result.confidence}")

asyncio.run(main())
```

### 使用工作流

```python
from ai_center import AlmondWorkflowManager, Settings
from ai_center.workflow.state import AlmondState

async def main():
    settings = Settings(dashscope_api_key="your-key")
    manager = AlmondWorkflowManager(settings)
    
    initial_state: AlmondState = {
        "title": "学习 Python",
        "content": "系统学习 Python 编程",
        # ... 其他字段
    }
    
    result = await manager.run_classification(initial_state)
    print(f"工作流结果: {result['classification']}")

asyncio.run(main())
```

## 🎉 完成！

服务已启动在 http://localhost:8000

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/v1/health

开始使用杏仁 AI-Center 吧！🌰