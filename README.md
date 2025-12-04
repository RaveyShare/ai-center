ai-center 服务用于对接多种大模型并提供统一 AI 能力，使用 FastAPI 与 LangChain。

运行：
- 依赖管理使用 `uv`
- 安装依赖：`cd ai-center && uv sync`
- 启动：`uv run uvicorn app.main:app --host 0.0.0.0 --port 8001`

环境变量：
- `JWT_SECRET` 用户中心一致的 HS256 密钥
- `OPENAI_API_KEY` OpenAI 密钥（可选）
- `ANTHROPIC_API_KEY` Anthropic 密钥（可选）

主要接口：
- `POST /v1/chat` 基于 LangChain 1.1 的统一聊天接口，支持 provider、model、temperature、max_tokens
