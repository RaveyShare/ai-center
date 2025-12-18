import os
from typing import List, Optional, Tuple
from langchain_openai import ChatOpenAI
from .base import Provider

class CompatibleProvider(Provider):
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None, base_url: Optional[str] = None, api_key: Optional[str] = None) -> Tuple[str, Optional[dict]]:
        # 如果没有传入 api_key，则尝试从环境变量获取，这里可以根据 model 或某种逻辑映射不同的模型环境变量
        # 但为了简单，我们优先使用传入的，或者通用的 COMPATIBLE_API_KEY
        actual_api_key = api_key or os.getenv("COMPATIBLE_API_KEY")
        actual_base_url = base_url or os.getenv("COMPATIBLE_BASE_URL")
        
        if not actual_api_key:
            raise ValueError("API Key missing for CompatibleProvider")
        
        chat = ChatOpenAI(
            model=model, 
            temperature=temperature, 
            max_tokens=max_tokens, 
            api_key=actual_api_key,
            base_url=actual_base_url
        )
        result = chat.invoke(self.to_lc_messages(messages))
        meta = getattr(result, "response_metadata", None)
        return result.content, meta
