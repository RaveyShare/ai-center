"""Brain 模块边角覆盖测试。

补充覆盖：
  - context_manager.estimate_tokens / build_compaction_prompt
  - LangGraphBrain checkpointer / compile_graph
  - Brain._maybe_compact 触发路径
  - Brain._get_llm 真实创建（用 MagicMock 替换 LLMFactory）
  - Hand.as_langchain_tool 默认实现
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from ravey.ai.agent_framework.brain.base import Brain, BrainConfig
from ravey.ai.agent_framework.brain.context_manager import (
    build_compaction_prompt,
    estimate_tokens,
)
from ravey.ai.agent_framework.brain.langgraph_brain import LangGraphBrain
from ravey.ai.agent_framework.hands.base import Hand
from ravey.ai.agent_framework.hands.local_hand import LocalHand
from ravey.ai.agent_framework.session.events import Event, EventType
from ravey.ai.agent_framework.session.store import MySQLSessionStore


@pytest.fixture
def store():
    s = MySQLSessionStore({
        "host": "127.0.0.1", "port": 3307, "user": "root",
        "password": "root", "database": "test_sessions",
    })
    s.setup()
    return s


@pytest.fixture
def hands():
    def add(a: int, b: int) -> int:
        """加。"""
        return a + b
    return {"add": LocalHand(add)}


@pytest.fixture
def config():
    return BrainConfig(
        agent_name="extras", system_prompt="测试",
        compaction_threshold=10,  # 极低，方便触发
    )


class TestContextManager:

    def test_estimate_tokens_handles_empty(self):
        assert estimate_tokens([]) == 0

    def test_estimate_tokens_counts_content_length(self):
        msgs = [HumanMessage(content="一" * 30)]
        assert estimate_tokens(msgs) == 10  # 30 // 3

    def test_estimate_tokens_handles_missing_content(self):
        msg = MagicMock()
        msg.content = None
        assert estimate_tokens([msg]) == 0

    def test_build_compaction_prompt(self):
        history = [HumanMessage(content="hello"), AIMessage(content="hi")]
        prompt = build_compaction_prompt(history)
        # 第一条是压缩指令，后面是历史
        assert isinstance(prompt[0], SystemMessage)
        assert "压缩" in prompt[0].content
        assert prompt[1:] == history


class TestLangGraphBrain:

    def test_checkpointer_property(self, store, hands, config):
        brain = LangGraphBrain(config=config, session_store=store, hands=hands)
        cp = brain.checkpointer
        assert cp is brain._checkpointer
        # MemorySaver 可以重复访问
        assert brain.checkpointer is cp

    def test_compile_graph(self, store, hands, config):
        brain = LangGraphBrain(config=config, session_store=store, hands=hands)

        # 构造一个最小 StateGraph
        from typing import TypedDict

        class S(TypedDict):
            x: int

        builder = StateGraph(S)
        builder.add_node("inc", lambda s: {"x": s["x"] + 1})
        builder.set_entry_point("inc")
        builder.add_edge("inc", END)

        compiled = brain.compile_graph(builder)
        assert compiled is not None
        assert brain.compiled_graph is compiled

    def test_compiled_graph_initially_none(self, store, hands, config):
        brain = LangGraphBrain(config=config, session_store=store, hands=hands)
        assert brain.compiled_graph is None


class TestBrainCompaction:

    def test_compact_triggers_when_threshold_exceeded(self, store, hands, config):
        sid = store.create_session("extras")
        # 写入一条很长的用户消息，方便触发压缩阈值
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "x" * 200},
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        # Mock LLM，让它在第一次调用时返回工具调用，触发 _maybe_compact
        mock_llm = MagicMock()
        seq = [0]

        def invoke(messages):
            seq[0] += 1
            if seq[0] == 1:
                msg = AIMessage(content="思考中")
                msg.tool_calls = [{"name": "add", "args": {"a": 1, "b": 2}, "id": "c1"}]
                return msg
            if seq[0] == 2:
                # 这是 _maybe_compact 内的压缩调用
                return AIMessage(content="对话摘要：用户问加法")
            return AIMessage(content="结果是 3")

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = invoke
        brain.set_llm(mock_llm)

        brain.run()

        # 应该有 COMPACTION 事件
        events = store.get_events(sid, event_types=[EventType.COMPACTION])
        assert len(events) == 1
        assert "对话摘要" in events[0].payload["summary"]


class TestBrainGetLLM:

    def test_get_llm_uses_factory_once(self, store, hands, config):
        brain = Brain(config=config, session_store=store, hands=hands)

        with patch(
            "ravey.ai.agent_framework.llm.LLMFactory",
        ) as factory_cls:
            instance = factory_cls.return_value
            instance.create.return_value = "fake-llm"

            llm1 = brain._get_llm()
            llm2 = brain._get_llm()

        # 同一个实例，只创建一次
        assert llm1 == "fake-llm"
        assert llm1 is llm2
        factory_cls.assert_called_once()


class TestBrainNoHands:

    def test_step_without_hands(self, store, config):
        sid = store.create_session("extras")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE, payload={"content": "hello"}
        ))

        brain = Brain(config=config, session_store=store, hands={})
        brain.wake(sid)

        mock_llm = MagicMock()
        # 没有 tools 时，bind_tools 不会被调用 → 直接 invoke
        resp = AIMessage(content="hi")
        resp.tool_calls = []
        mock_llm.invoke.return_value = resp
        brain.set_llm(mock_llm)

        result = brain.step()
        assert result is False
        # bind_tools 不应被调用（hands 为空）
        mock_llm.bind_tools.assert_not_called()


class TestBrainRunRespectsMaxToolCalls:

    def test_run_stops_at_max_tool_calls(self, store, hands):
        sid = store.create_session("extras")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE, payload={"content": "loop"}
        ))

        cfg = BrainConfig(
            agent_name="extras", system_prompt="测试",
            max_tool_calls=2,
        )
        brain = Brain(config=cfg, session_store=store, hands=hands)
        brain.wake(sid)

        mock_llm = MagicMock()

        def invoke(_):
            msg = AIMessage(content="")
            msg.tool_calls = [{"name": "add", "args": {"a": 1, "b": 1}, "id": "c"}]
            return msg

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = invoke
        brain.set_llm(mock_llm)

        brain.run()
        # 不会无限循环；max_tool_calls=2 应该最多调用 2+1 次
        assert mock_llm.invoke.call_count <= 3


class TestHandBaseFallback:

    def test_default_as_langchain_tool(self):
        """Hand 抽象基类的默认 as_langchain_tool 实现。"""

        class FakeHand(Hand):
            @property
            def name(self) -> str:
                return "fake"

            def execute(self, name, input):
                return f"got {input}"

            def schema(self):
                return {"name": "fake", "description": "Fake tool"}

        hand = FakeHand()
        lc = hand.as_langchain_tool()
        assert lc.name == "fake"
        result = lc.invoke({"x": 1})
        assert "got" in result
