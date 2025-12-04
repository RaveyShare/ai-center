from fastapi import FastAPI, Header
from .schemas import ChatRequest, ChatResponse
from .auth import verify_token
from .providers import get_provider

app = FastAPI(title="ai-center")

@app.post("/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest, authorization: str = Header(None)):
    verify_token(authorization)
    provider = get_provider(req.provider)
    content, usage = provider.generate(model=req.model, messages=[m.model_dump() for m in req.messages], temperature=req.temperature, max_tokens=req.max_tokens)
    return ChatResponse(content=content, usage=usage)

