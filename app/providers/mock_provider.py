from typing import List, Optional, Tuple
from .base import Provider

class MockProvider(Provider):
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Tuple[str, Optional[dict]]:
        joined = "\n".join(m["content"] for m in messages)
        return f"[mock:{model}] {joined}", {"provider": "mock"}

