import os
from typing import List, Optional, Tuple
from langchain_anthropic import ChatAnthropic
from .base import Provider

class AnthropicProvider(Provider):
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Tuple[str, Optional[dict]]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY missing")
        chat = ChatAnthropic(model=model, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
        result = chat.invoke(self.to_lc_messages(messages))
        meta = getattr(result, "response_metadata", None)
        return result.content, meta

