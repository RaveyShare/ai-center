from fastapi import FastAPI, Header
from contextlib import asynccontextmanager
from .nacos import nacos_manager
from .schemas import ChatRequest, ChatResponse
from .auth import verify_token
from .providers import get_provider
from .routers import ai

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: register with Nacos
    nacos_manager.register()
    yield
    # Shutdown: deregister
    nacos_manager.deregister()

app = FastAPI(title="ai-center", lifespan=lifespan)

app.include_router(ai.router)

@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, authorization: str = Header(None)):
    verify_token(authorization)
    provider = get_provider(req.provider)
    
    # 构建生成参数
    gen_params = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
        "temperature": req.temperature,
        "max_tokens": req.max_tokens
    }
    
    # 如果是 CompatibleProvider 或者支持动态参数的，可以传入
    if req.provider in ["deepseek", "qwen", "kimi", "compatible"]:
        gen_params["base_url"] = req.base_url
        gen_params["api_key"] = req.api_key
        
    content, usage = provider.generate(**gen_params)
    return ChatResponse(content=content, usage=usage)

