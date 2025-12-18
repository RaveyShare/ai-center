import os
from typing import List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from .base import Provider

class GeminiProvider(Provider):
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Tuple[str, Optional[dict]]:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY missing")
        
        chat = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key
        )
        result = chat.invoke(self.to_lc_messages(messages))
        meta = getattr(result, "response_metadata", None)
        return result.content, meta
