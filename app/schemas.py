from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    provider: Literal["openai", "anthropic", "mock"]
    model: str
    messages: List[Message]
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)

class ChatResponse(BaseModel):
    content: str
    usage: Optional[dict] = None
