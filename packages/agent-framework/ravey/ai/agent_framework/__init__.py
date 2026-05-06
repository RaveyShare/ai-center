"""ravey.ai.agent_framework —— 基于 LangGraph 的 Agent 工程脚手架。

三层抽象：
    - Brain：无状态 Agent 推理循环（wake → step → run → 崩溃可恢复）
    - Hand：统一的工具执行接口（本地函数 / MCP / 沙箱）
    - Session：append-only 事件日志，独立于 Brain 的持久层

最小用法：
    from ravey.ai.agent_framework import (
        Brain, BrainConfig,
        LocalHand,
        MySQLSessionStore,
    )

    store = MySQLSessionStore(conn_config); store.setup()
    sid = store.create_session("my-agent")

    brain = Brain(
        config=BrainConfig(agent_name="my-agent", system_prompt="..."),
        session_store=store,
        hands={"my_tool": LocalHand(my_tool)},
    )
    brain.wake(sid)
    reply = brain.run()
"""

from ravey.ai.agent_framework.session import (
    Event,
    EventType,
    SessionMeta,
    SessionStore,
    MySQLSessionStore,
)
from ravey.ai.agent_framework.brain import (
    Brain,
    BrainConfig,
    LangGraphBrain,
    BrainOrchestrator,
)
from ravey.ai.agent_framework.hands import Hand, LocalHand, MCPHand

__all__ = [
    "Event",
    "EventType",
    "SessionMeta",
    "SessionStore",
    "MySQLSessionStore",
    "Brain",
    "BrainConfig",
    "LangGraphBrain",
    "BrainOrchestrator",
    "Hand",
    "LocalHand",
    "MCPHand",
]

__version__ = "0.1.0"