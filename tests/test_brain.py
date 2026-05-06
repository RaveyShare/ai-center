"""Brain 测试。

使用 Mock LLM 和 MySQL SessionStore 测试 Brain 的核心循环。
测试覆盖: wake 恢复 / step 单步 / run 完整循环 / 工具路由 / 未知工具处理
"""

import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from ravey.ai.agent_framework.brain.base import Brain, BrainConfig
from ravey.ai.agent_framework.brain.orchestrator import BrainOrchestrator
from ravey.ai.agent_framework.hands.local_hand import LocalHand
from ravey.ai.agent_framework.session.store import MySQLSessionStore
from ravey.ai.agent_framework.session.events import Event, EventType


# ====== 测试用工具 ======

def add(a: int, b: int) -> int:
    """两数相加。"""
    return a + b


def greet(name: str) -> str:
    """打招呼。"""
    return f"Hello, {name}!"


@pytest.fixture
def store():
    """测试用 MySQL SessionStore。"""
    s = MySQLSessionStore({
        "host": "127.0.0.1",
        "port": 3307,
        "user": "root",
        "password": "root",
        "database": "test_sessions",
    })
    s.setup()
    return s


@pytest.fixture
def hands():
    """测试用 Hand 集合。"""
    add_hand = LocalHand(add, zone="green", tags=["math"])
    greet_hand = LocalHand(greet, zone="green", tags=["greeting"])
    return {"add": add_hand, "greet": greet_hand}


@pytest.fixture
def config():
    return BrainConfig(
        agent_name="test-brain",
        system_prompt="你是一个测试助手。",
        llm_provider="dashscope",
        llm_model="qwen-plus",
    )


class TestBrain:

    def test_wake_empty_session(self, store, hands, config):
        """从空 Session 唤醒。"""
        sid = store.create_session("test-brain")
        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)
        # wake 后应该有一个 SYSTEM 事件
        events = store.get_events(sid)
        assert len(events) == 1
        assert events[0].event_type == EventType.SYSTEM
        assert events[0].payload["action"] == "brain_wake"

    def test_step_no_tool_call(self, store, hands, config):
        """LLM 不调用工具时，step 返回 False。"""
        sid = store.create_session("test-brain")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "你好"}
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        # Mock LLM 返回无工具调用的响应
        mock_llm = MagicMock()
        mock_response = AIMessage(content="你好！有什么可以帮助你的？")
        mock_response.tool_calls = []
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        brain.set_llm(mock_llm)

        result = brain.step()
        assert result is False

    def test_step_with_tool_call(self, store, hands, config):
        """LLM 调用工具时，step 返回 True。"""
        sid = store.create_session("test-brain")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "1+2等于几？"}
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        # Mock LLM 返回带工具调用的响应
        mock_llm = MagicMock()
        mock_response = AIMessage(content="让我算一下")
        mock_response.tool_calls = [
            {"name": "add", "args": {"a": 1, "b": 2}, "id": "call_001"}
        ]
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = mock_response
        brain.set_llm(mock_llm)

        result = brain.step()
        assert result is True

        # 验证事件记录
        events = store.get_events(sid, event_types=[EventType.TOOL_RESULT])
        assert len(events) == 1
        assert events[0].payload["result"] == "3"

    def test_run_full_cycle(self, store, hands, config):
        """完整的 run 循环: 工具调用 → 最终回复。"""
        sid = store.create_session("test-brain")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "1+2等于几？"}
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        # 第一次调用返回工具调用，第二次返回最终回复
        mock_llm = MagicMock()
        call_count = [0]

        def mock_invoke(messages):
            call_count[0] += 1
            if call_count[0] == 1:
                msg = AIMessage(content="")
                msg.tool_calls = [
                    {"name": "add", "args": {"a": 1, "b": 2}, "id": "call_001"}
                ]
                return msg
            else:
                return AIMessage(content="1+2=3")

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = mock_invoke
        brain.set_llm(mock_llm)

        result = brain.run()
        assert result == "1+2=3"
        assert call_count[0] == 2

        # Session 状态应为 completed
        session = store.get_session(sid)
        assert session.status == "completed"

    def test_unknown_tool(self, store, hands, config):
        """调用未知工具时返回错误。"""
        sid = store.create_session("test-brain")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "test"}
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        mock_llm = MagicMock()
        # 第一次返回未知工具调用
        call_count = [0]

        def mock_invoke(messages):
            call_count[0] += 1
            if call_count[0] == 1:
                msg = AIMessage(content="")
                msg.tool_calls = [
                    {"name": "unknown_tool", "args": {}, "id": "call_002"}
                ]
                return msg
            else:
                return AIMessage(content="抱歉，工具不存在。")

        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = mock_invoke
        brain.set_llm(mock_llm)

        result = brain.run()
        assert "抱歉" in result

        # 检查 TOOL_RESULT 中包含错误信息
        events = store.get_events(sid, event_types=[EventType.TOOL_RESULT])
        assert any("unknown tool" in e.payload["result"] for e in events)

    def test_wake_restores_messages(self, store, hands, config):
        """wake 从已有事件恢复消息。"""
        sid = store.create_session("test-brain")
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "hello"}
        ))
        store.emit_event(sid, Event(
            event_type=EventType.LLM_RESPONSE,
            payload={"content": "Hi there!", "tool_calls": []}
        ))
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "how are you?"}
        ))

        brain = Brain(config=config, session_store=store, hands=hands)
        brain.wake(sid)

        # 应恢复 3 条消息
        assert len(brain._messages) == 3
        assert isinstance(brain._messages[0], HumanMessage)
        assert isinstance(brain._messages[1], AIMessage)
        assert isinstance(brain._messages[2], HumanMessage)


class TestBrainOrchestrator:

    def test_register_and_get(self, store, hands, config):
        orch = BrainOrchestrator(session_store=store)
        brain = orch.register_brain(config=config, hands=hands)
        assert orch.get_brain("test-brain") is brain
        assert "test-brain" in orch.list_brains()

    def test_wake_brain(self, store, hands, config):
        sid = store.create_session("test-brain")
        orch = BrainOrchestrator(session_store=store)
        orch.register_brain(config=config, hands=hands)
        brain = orch.wake_brain("test-brain", sid)
        assert brain._session_id == sid

    def test_unknown_brain_raises(self, store):
        orch = BrainOrchestrator(session_store=store)
        with pytest.raises(ValueError, match="Unknown brain"):
            orch.wake_brain("nonexistent", "fake-session-id")
