"""BrainOrchestrator — 多 Brain 管理器。

在需要多个 Agent 协作的场景中，Orchestrator 负责：
1. 创建和管理多个 Brain 实例
2. 在 Brain 之间路由消息
3. 管理共享 Session

典型场景: 主 Agent 调用子 Agent（如 planning → coding → review）
"""

from typing import Any

from ravey.ai.agent_framework.brain.base import Brain, BrainConfig
from ravey.ai.agent_framework.session.store import SessionStore
from ravey.ai.agent_framework.hands.base import Hand


class BrainOrchestrator:
    """多 Brain 编排器。"""

    def __init__(self, session_store: SessionStore):
        self._session_store = session_store
        self._brains: dict[str, Brain] = {}

    def register_brain(
        self,
        config: BrainConfig,
        hands: dict[str, Hand],
    ) -> Brain:
        """注册一个 Brain。"""
        brain = Brain(config=config, session_store=self._session_store, hands=hands)
        self._brains[config.agent_name] = brain
        return brain

    def get_brain(self, agent_name: str) -> Brain | None:
        """获取已注册的 Brain。"""
        return self._brains.get(agent_name)

    def wake_brain(self, agent_name: str, session_id: str) -> Brain:
        """唤醒指定 Brain 并恢复 Session。"""
        brain = self._brains.get(agent_name)
        if brain is None:
            raise ValueError(f"Unknown brain: {agent_name}")
        brain.wake(session_id)
        return brain

    def list_brains(self) -> list[str]:
        """列出所有已注册的 Brain 名称。"""
        return list(self._brains.keys())
