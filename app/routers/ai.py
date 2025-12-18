from fastapi import APIRouter, Header, Depends
from ..schemas import ChatResponse, ChatRequest
from ..auth import verify_token
from ..providers import get_provider
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/v1/ai/workflow", tags=["workflow"])

class MemoryWorkflowRequest(BaseModel):
    title: str
    content: str
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4o"

class DecomposeWorkflowRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    provider: Optional[str] = "openai"
    model: Optional[str] = "gpt-4o"

@router.post("/memory", response_model=ChatResponse)
def memory_workflow(req: MemoryWorkflowRequest, authorization: str = Header(None)):
    verify_token(authorization)
    provider = get_provider(req.provider)
    
    # 这里先实现基础逻辑，后续 Phase 4 会引入 LangGraph
    prompt = f"你是一个记忆专家。请为以下内容生成记忆助记（包含心智图结构、口诀、感官联想）：\n标题：{req.title}\n内容：{req.content}"
    messages = [
        {"role": "system", "content": "你是一个专业的记忆辅助专家。"},
        {"role": "user", "content": prompt}
    ]
    
    content, usage = provider.generate(model=req.model, messages=messages)
    return ChatResponse(content=content, usage=usage)

@router.post("/decompose", response_model=ChatResponse)
def decompose_workflow(req: DecomposeWorkflowRequest, authorization: str = Header(None)):
    verify_token(authorization)
    provider = get_provider(req.provider)
    
    prompt = f"你是一个项目管理专家。请将以下任务分解为更小的、可执行的子任务：\n任务标题：{req.title}\n任务描述：{req.description}\n请以JSON格式返回子任务列表。"
    messages = [
        {"role": "system", "content": "你是一个专业的任务拆解专家。"},
        {"role": "user", "content": prompt}
    ]
    
    content, usage = provider.generate(model=req.model, messages=messages)
    return ChatResponse(content=content, usage=usage)
