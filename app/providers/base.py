from typing import List, Optional, Tuple
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

class Provider:
    def to_lc_messages(self, messages: List[dict]) -> List[BaseMessage]:
        out: List[BaseMessage] = []
        for m in messages:
            if m["role"] == "system":
                out.append(SystemMessage(content=m["content"]))
            elif m["role"] == "user":
                out.append(HumanMessage(content=m["content"]))
            else:
                out.append(AIMessage(content=m["content"]))
        return out
    def generate(self, model: str, messages: List[dict], temperature: float = 0.7, max_tokens: Optional[int] = None) -> Tuple[str, Optional[dict]]:
        raise NotImplementedError

