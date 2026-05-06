"""Session Store 测试。

使用 Docker MySQL 运行。
测试覆盖: 建表幂等 / 事件追加 / 切片读取 / seq 单调递增 / 类型过滤
"""

import pytest
from ravey.ai.agent_framework.session.store import MySQLSessionStore
from ravey.ai.agent_framework.session.events import Event, EventType


@pytest.fixture
def store():
    """创建测试用 SessionStore。

    需要本地 MySQL:
        docker run -d --name test-mysql -e MYSQL_ROOT_PASSWORD=root \
            -e MYSQL_DATABASE=test_sessions -p 3307:3306 mysql:8.0
    """
    s = MySQLSessionStore({
        "host": "127.0.0.1",
        "port": 3307,
        "user": "root",
        "password": "root",
        "database": "test_sessions",
    })
    s.setup()
    return s


class TestSessionStore:

    def test_setup_idempotent(self, store):
        """建表可重复执行。"""
        store.setup()
        store.setup()  # 不报错

    def test_create_and_get_session(self, store):
        sid = store.create_session("test-agent", {"model": "qwen"})
        session = store.get_session(sid)
        assert session is not None
        assert session.agent_name == "test-agent"
        assert session.status == "active"
        assert session.event_count == 0

    def test_emit_and_get_events(self, store):
        sid = store.create_session("test-agent")

        # 追加 3 个事件
        store.emit_event(sid, Event(event_type=EventType.USER_MESSAGE, payload={"content": "hello"}))
        store.emit_event(sid, Event(event_type=EventType.LLM_RESPONSE, payload={"content": "hi"}))
        store.emit_event(sid, Event(event_type=EventType.USER_MESSAGE, payload={"content": "bye"}))

        # 全量读取
        events = store.get_events(sid)
        assert len(events) == 3
        assert events[0].seq == 0
        assert events[1].seq == 1
        assert events[2].seq == 2

        # 切片读取
        events = store.get_events(sid, start=1, end=2)
        assert len(events) == 2
        assert events[0].event_type == EventType.LLM_RESPONSE

    def test_event_type_filter(self, store):
        sid = store.create_session("test-agent")
        store.emit_event(sid, Event(event_type=EventType.USER_MESSAGE, payload={"content": "q1"}))
        store.emit_event(sid, Event(event_type=EventType.LLM_RESPONSE, payload={"content": "a1"}))
        store.emit_event(sid, Event(event_type=EventType.TOOL_CALL, payload={"name": "search"}))
        store.emit_event(sid, Event(event_type=EventType.USER_MESSAGE, payload={"content": "q2"}))

        # 只取 user_message
        events = store.get_events(sid, event_types=[EventType.USER_MESSAGE])
        assert len(events) == 2
        assert all(e.event_type == EventType.USER_MESSAGE for e in events)

    def test_seq_monotonic(self, store):
        """seq 严格单调递增。"""
        sid = store.create_session("test-agent")
        for i in range(10):
            seq = store.emit_event(sid, Event(
                event_type=EventType.SYSTEM, payload={"i": i}
            ))
            assert seq == i

    def test_session_status_update(self, store):
        sid = store.create_session("test-agent")
        store.update_status(sid, "completed")
        session = store.get_session(sid)
        assert session.status == "completed"
