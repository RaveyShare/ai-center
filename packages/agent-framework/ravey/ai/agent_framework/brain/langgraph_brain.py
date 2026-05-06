"""LangGraph StateGraph 实现的 Brain。

在基础 Brain 的 step/run 循环之上，提供 LangGraph StateGraph 集成。
使用 MemorySaver 作为内存级 checkpointer，长期持久化由 SessionStore 负责。
"""

from typing import Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ravey.ai.agent_framework.brain.base import Brain, BrainConfig
from ravey.ai.agent_framework.session.store import SessionStore
from ravey.ai.agent_framework.hands.base import Hand


class LangGraphBrain(Brain):
    """基于 LangGraph StateGraph 的 Brain 实现。

    在 Brain.run() 的基础上，增加 LangGraph graph 编排能力。
    适用于需要复杂状态流转的场景（如多步骤 pipeline）。
    """

    def __init__(
        self,
        config: BrainConfig,
        session_store: SessionStore,
        hands: dict[str, Hand],
        graph_builder: StateGraph | None = None,
    ):
        super().__init__(config, session_store, hands)
        self._checkpointer = MemorySaver()
        self._graph_builder = graph_builder
        self._compiled_graph = None

    @property
    def checkpointer(self) -> MemorySaver:
        return self._checkpointer

    def compile_graph(self, graph_builder: StateGraph) -> Any:
        """编译 StateGraph，注入 checkpointer。"""
        self._compiled_graph = graph_builder.compile(checkpointer=self._checkpointer)
        return self._compiled_graph

    @property
    def compiled_graph(self):
        return self._compiled_graph
