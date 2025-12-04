import os
from typing import List, Optional, Tuple
from langchain_openai import ChatOpenAI
from .base import Provider

class OpenAIProvider(Provider):
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Tuple[str, Optional[dict]]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY missing")
        chat = ChatOpenAI(model=model, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        result = chat.invoke(self.to_lc_messages(messages))
        meta = getattr(result, "response_metadata", None)
        return result.content, meta

