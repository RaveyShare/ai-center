"""Session 事件定义。

所有 Brain 的行为都记录为 Event，写入 Session Store。
Event 是不可变的，一旦写入不修改。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time


class EventType(str, Enum):
    USER_MESSAGE = "user_message"       # 用户输入
    LLM_REQUEST = "llm_request"         # LLM 调用请求（记录 model、message_count）
    LLM_RESPONSE = "llm_response"       # LLM 返回（content + tool_calls）
    TOOL_CALL = "tool_call"             # Brain → Hand 的调用
    TOOL_RESULT = "tool_result"         # Hand → Brain 的返回
    ERROR = "error"                     # 错误
    COMPACTION = "compaction"           # Context 压缩（摘要替代历史消息）
    CHECKPOINT = "checkpoint"           # LangGraph state snapshot（可选）
    SYSTEM = "system"                   # 系统事件（brain_wake / brain_crash 等）


@dataclass
class Event:
    """单个事件。"""
    event_type: EventType
    payload: dict[str, Any]
    seq: int = -1                      # 由 SessionStore 分配
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class SessionMeta:
    """Session 元信息。"""
    id: str
    agent_name: str
    status: str                        # active / paused / completed / failed
    config: dict[str, Any]
    created_at: str
    updated_at: str
    event_count: int = 0
