"""集成测试：基于任务规划场景的端到端验证。

覆盖：
  - SessionStore 创建 / 事件追加
  - Brain wake → run 完整循环（mock LLM 模拟工具调用链）
  - Brain 崩溃后从 Session 恢复
  - BrainOrchestrator 多 Brain 管理
"""

import pytest
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from ravey.ai.agent_framework.brain import Brain, BrainConfig, BrainOrchestrator
from ravey.ai.agent_framework.session import (
    Event, EventType, MySQLSessionStore,
)

from ravey.ai.tasks.agent import AGENT_NAME, SYSTEM_PROMPT, build_brain
from ravey.ai.tasks.tools import build_hands


@pytest.fixture
def store():
    s = MySQLSessionStore({
        "host": "127.0.0.1",
        "port": 3307,
        "user": "root",
        "password": "root",
        "database": "test_sessions",
    })
    s.setup()
    return s


def _make_planner_brain(store):
    """创建挂着任务规划工具的 Brain。"""
    brain = build_brain(store)
    return brain


def _mock_planner_llm():
    """构造一个按 collect → split → estimate → schedule → save → final 顺序回复的 mock LLM。"""
    mock_llm = MagicMock()
    counter = {"i": 0}

    def invoke(messages):
        counter["i"] += 1
        i = counter["i"]
        if i == 1:
            msg = AIMessage(content="")
            msg.tool_calls = [{
                "name": "parse_requirement",
                "args": {"text": "- 接口A\n- 修复登录 bug"},
                "id": "c1",
            }]
            return msg
        if i == 2:
            msg = AIMessage(content="")
            msg.tool_calls = [{
                "name": "split_task",
                "args": {"task": {"id": "t1", "title": "接口A"}},
                "id": "c2",
            }]
            return msg
        if i == 3:
            msg = AIMessage(content="")
            msg.tool_calls = [{
                "name": "estimate_effort",
                "args": {"task": {"id": "t1", "title": "接口A", "subtasks": []}},
                "id": "c3",
            }]
            return msg
        if i == 4:
            msg = AIMessage(content="")
            msg.tool_calls = [{
                "name": "schedule_tasks",
                "args": {"task_tree": [{"id": "t1", "title": "接口A", "hours": 4.0, "subtasks": []}]},
                "id": "c4",
            }]
            return msg
        return AIMessage(content="规划完成：1 个任务、4 小时")

    mock_llm.bind_tools.return_value = mock_llm
    mock_llm.invoke.side_effect = invoke
    return mock_llm


class TestEndToEndPlanner:

    def test_full_planning_flow(self, store):
        """完整规划流程：用户消息 → Brain 调用 4 个工具 → 输出摘要。"""
        sid = store.create_session(AGENT_NAME)
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "请帮我规划：接口A、修复登录 bug"},
        ))

        brain = _make_planner_brain(store)
        brain.set_llm(_mock_planner_llm())
        brain.wake(sid)
        reply = brain.run()

        assert "规划完成" in reply

        all_events = store.get_events(sid)
        types = [e.event_type for e in all_events]
        assert EventType.USER_MESSAGE in types
        assert EventType.SYSTEM in types
        assert EventType.LLM_REQUEST in types
        assert EventType.LLM_RESPONSE in types
        assert EventType.TOOL_CALL in types
        assert EventType.TOOL_RESULT in types

        # 至少四次工具调用：parse / split / estimate / schedule
        tool_calls = [e for e in all_events if e.event_type == EventType.TOOL_CALL]
        assert len(tool_calls) >= 4
        called_names = {tc.payload["name"] for tc in tool_calls}
        assert {"parse_requirement", "split_task", "estimate_effort", "schedule_tasks"} <= called_names

        meta = store.get_session(sid)
        assert meta.status == "completed"

    def test_brain_crash_recovery(self, store):
        """Brain 崩溃后，新实例从 Session 事件日志恢复消息上下文。"""
        sid = store.create_session(AGENT_NAME)
        # 模拟 Brain 崩溃前的事件
        store.emit_event(sid, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": "规划任务"},
        ))
        store.emit_event(sid, Event(
            event_type=EventType.LLM_RESPONSE,
            payload={
                "content": "",
                "tool_calls": [{"name": "parse_requirement", "args": {"text": "x"}, "id": "c1"}],
            },
        ))
        store.emit_event(sid, Event(
            event_type=EventType.TOOL_RESULT,
            payload={"tool_call_id": "c1", "name": "parse_requirement", "result": "[]"},
        ))

        new_brain = _make_planner_brain(store)
        mock = MagicMock()
        mock.bind_tools.return_value = mock
        mock.invoke.return_value = AIMessage(content="任务列表为空，未生成规划。")
        new_brain.set_llm(mock)
        new_brain.wake(sid)

        assert len(new_brain._messages) == 3
        reply = new_brain.run()
        assert "任务列表" in reply

    def test_orchestrator_multi_brain(self, store):
        """Orchestrator 同时管理两个 Brain。"""
        orch = BrainOrchestrator(session_store=store)
        hands = build_hands()
        orch.register_brain(BrainConfig(agent_name="planner-a", system_prompt="P-A"), hands)
        orch.register_brain(BrainConfig(agent_name="planner-b", system_prompt="P-B"), hands)

        assert sorted(orch.list_brains()) == ["planner-a", "planner-b"]

        sa = store.create_session("planner-a")
        sb = store.create_session("planner-b")
        ba = orch.wake_brain("planner-a", sa)
        bb = orch.wake_brain("planner-b", sb)
        assert ba._session_id == sa
        assert bb._session_id == sb

    def test_event_filtering_by_type_and_range(self, store):
        """事件类型 + 切片过滤。"""
        sid = store.create_session(AGENT_NAME)
        for i in range(3):
            store.emit_event(sid, Event(
                event_type=EventType.USER_MESSAGE, payload={"i": i},
            ))
            store.emit_event(sid, Event(
                event_type=EventType.LLM_RESPONSE, payload={"i": i},
            ))

        only_user = store.get_events(sid, event_types=[EventType.USER_MESSAGE])
        assert len(only_user) == 3

        sliced = store.get_events(sid, start=2, end=4)
        assert [e.seq for e in sliced] == [2, 3, 4]

    def test_agent_constants(self):
        """agent 模块的常量在符合约束。"""
        assert AGENT_NAME == "task-planner"
        assert "TaskPlannerAgent" in SYSTEM_PROMPT
        assert "parse_requirement" in SYSTEM_PROMPT
