"""Session Store — Brain 之外的独立持久层。

设计原则（来自 Anthropic Managed Agents）：
1. append-only: 事件只追加，不修改不删除
2. 独立于 Brain 生命周期: Brain 崩溃不影响 Session
3. 支持切片读取: Brain 可以选择性加载上下文（getEvents 支持 start/end）
4. 支持多 Brain 共享: 不同 Brain 实例可以读同一个 Session

MySQL 实现要点：
- sessions 表: 元信息
- session_events 表: 事件日志，(session_id, seq) 唯一
- seq 由 store 分配，保证单调递增
"""

from typing import Protocol, runtime_checkable
import json
import uuid

import pymysql

from ravey.ai.agent_framework.session.events import Event, EventType, SessionMeta


@runtime_checkable
class SessionStore(Protocol):
    """Session Store 协议。

    任何实现此协议的类都可以作为 Session 后端。
    当前提供 MySQLSessionStore，未来可以加 PostgreSQL / Redis Stream 等。
    """

    def setup(self) -> None:
        """创建表结构（幂等）。"""
        ...

    def create_session(self, agent_name: str, config: dict | None = None) -> str:
        """创建新 Session，返回 session_id。"""
        ...

    def emit_event(self, session_id: str, event: Event) -> int:
        """追加事件到 Session，返回分配的 seq。"""
        ...

    def get_events(
        self, session_id: str,
        start: int = 0,
        end: int = -1,
        event_types: list[EventType] | None = None
    ) -> list[Event]:
        """读取事件。

        Args:
            start: 起始 seq（包含）
            end: 结束 seq（包含），-1 表示到最后
            event_types: 可选过滤，只返回指定类型的事件
        """
        ...

    def get_session(self, session_id: str) -> SessionMeta | None:
        """获取 Session 元信息。"""
        ...

    def update_status(self, session_id: str, status: str) -> None:
        """更新 Session 状态。"""
        ...


class MySQLSessionStore:
    """MySQL 实现的 Session Store。

    依赖: pymysql
    连接配置通过 conn_config dict 传入:
        {"host": "...", "port": 3306, "user": "...", "password": "...", "database": "..."}
    """

    def __init__(self, conn_config: dict):
        self._conn_config = conn_config

    def _get_conn(self):
        return pymysql.connect(
            **self._conn_config,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

    def setup(self) -> None:
        """建表（幂等）。"""
        from ravey.ai.agent_framework.session.migrations import CREATE_TABLES_SQL
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                for sql in CREATE_TABLES_SQL:
                    cur.execute(sql)
            conn.commit()
        finally:
            conn.close()

    def create_session(self, agent_name: str, config: dict | None = None) -> str:
        session_id = str(uuid.uuid4())
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO agent_sessions (id, agent_name, config) VALUES (%s, %s, %s)",
                    (session_id, agent_name, json.dumps(config or {}))
                )
            conn.commit()
        finally:
            conn.close()
        return session_id

    def emit_event(self, session_id: str, event: Event) -> int:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                # 原子分配 seq: SELECT FOR UPDATE 模式
                cur.execute(
                    "SELECT COALESCE(MAX(seq), -1) + 1 as next_seq "
                    "FROM agent_session_events WHERE session_id = %s FOR UPDATE",
                    (session_id,)
                )
                next_seq = cur.fetchone()["next_seq"]
                cur.execute(
                    "INSERT INTO agent_session_events "
                    "(session_id, seq, event_type, payload, created_at) "
                    "VALUES (%s, %s, %s, %s, FROM_UNIXTIME(%s))",
                    (session_id, next_seq, event.event_type.value,
                     json.dumps(event.payload, ensure_ascii=False, default=str),
                     event.timestamp)
                )
                # 更新 session 的 updated_at
                cur.execute(
                    "UPDATE agent_sessions SET updated_at = NOW() WHERE id = %s",
                    (session_id,)
                )
            conn.commit()
            return next_seq
        finally:
            conn.close()

    def get_events(
        self, session_id: str,
        start: int = 0,
        end: int = -1,
        event_types: list[EventType] | None = None
    ) -> list[Event]:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                sql = "SELECT * FROM agent_session_events WHERE session_id = %s AND seq >= %s"
                params: list = [session_id, start]

                if end != -1:
                    sql += " AND seq <= %s"
                    params.append(end)

                if event_types:
                    placeholders = ",".join(["%s"] * len(event_types))
                    sql += f" AND event_type IN ({placeholders})"
                    params.extend([et.value for et in event_types])

                sql += " ORDER BY seq ASC"
                cur.execute(sql, params)
                rows = cur.fetchall()

                return [
                    Event(
                        event_type=EventType(r["event_type"]),
                        payload=(json.loads(r["payload"])
                                 if isinstance(r["payload"], str)
                                 else r["payload"]),
                        seq=r["seq"],
                        session_id=session_id,
                        timestamp=r["created_at"].timestamp() if r["created_at"] else 0,
                    )
                    for r in rows
                ]
        finally:
            conn.close()

    def get_session(self, session_id: str) -> SessionMeta | None:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM agent_sessions WHERE id = %s", (session_id,))
                row = cur.fetchone()
                if not row:
                    return None

                cur.execute(
                    "SELECT COUNT(*) as cnt FROM agent_session_events WHERE session_id = %s",
                    (session_id,)
                )
                count = cur.fetchone()["cnt"]

                return SessionMeta(
                    id=row["id"],
                    agent_name=row["agent_name"],
                    status=row["status"],
                    config=json.loads(row["config"]) if isinstance(row["config"], str) else row["config"],
                    created_at=str(row["created_at"]),
                    updated_at=str(row["updated_at"]),
                    event_count=count,
                )
        finally:
            conn.close()

    def update_status(self, session_id: str, status: str) -> None:
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE agent_sessions SET status = %s WHERE id = %s",
                    (status, session_id)
                )
            conn.commit()
        finally:
            conn.close()
