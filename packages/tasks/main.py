"""Babycare AI Agent 应用入口。

启动逻辑（v3）：
    1. 读取 agent_config.yaml
    2. 初始化 SessionStore（MySQL）
    3. 创建 BrainOrchestrator，注册 task-planner Brain
    4. 拉起 FastAPI（带 Session API 路由）
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ravey.ai.agent_framework.brain import BrainOrchestrator
from ravey.ai.agent_framework.session import Event, EventType, MySQLSessionStore

from ravey.ai.tasks.agent import AGENT_NAME, build_brain


# ====== 配置加载 ======

def _expand_env(value):
    """递归把 ${VAR} / ${VAR:default} 替换为环境变量。"""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        body = value[2:-1]
        var, _, default = body.partition(":")
        return os.environ.get(var, default)
    if isinstance(value, dict):
        return {k: _expand_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env(v) for v in value]
    return value


def load_config(path: str | Path = "agent_config.yaml") -> dict:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return _expand_env(raw or {})


# ====== 应用工厂 ======

class CreateSessionReq(BaseModel):
    user_id: str | None = None


class MessageReq(BaseModel):
    message: str = Field(..., min_length=1)


def create_app(config: dict | None = None) -> FastAPI:
    config = config or load_config()

    # 1. SessionStore
    session_cfg = config["session"]
    store = MySQLSessionStore({
        "host": session_cfg["host"],
        "port": int(session_cfg["port"]),
        "user": session_cfg["user"],
        "password": session_cfg["password"],
        "database": session_cfg["database"],
    })
    store.setup()

    # 2. Orchestrator + Brain
    orchestrator = BrainOrchestrator(session_store=store)
    llm_providers = config.get("llm", {}).get("providers", {})
    provider, provider_cfg = next(iter(llm_providers.items()), ("dashscope", {}))

    brain = build_brain(
        store,
        llm_provider=provider,
        llm_model=provider_cfg.get("default_model", "qwen-plus"),
    )
    orchestrator._brains[AGENT_NAME] = brain

    # 3. FastAPI
    app = FastAPI(
        title=config.get("server", {}).get("title", "Babycare AI Agent API"),
        version=config.get("server", {}).get("version", "0.1.0"),
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "agent": AGENT_NAME}

    @app.post("/session")
    async def create_session(req: CreateSessionReq):
        sid = store.create_session(AGENT_NAME, {"user_id": req.user_id})
        return {"session_id": sid}

    @app.get("/session/{session_id}")
    async def get_session(session_id: str):
        meta = store.get_session(session_id)
        if meta is None:
            raise HTTPException(404, f"Session not found: {session_id}")
        return {
            "id": meta.id,
            "agent_name": meta.agent_name,
            "status": meta.status,
            "config": meta.config,
            "event_count": meta.event_count,
        }

    @app.get("/session/{session_id}/events")
    async def get_events(session_id: str, start: int = 0, end: int = -1):
        events = store.get_events(session_id, start=start, end=end)
        return [
            {
                "seq": e.seq,
                "event_type": e.event_type.value,
                "payload": e.payload,
                "timestamp": e.timestamp,
            }
            for e in events
        ]

    @app.post("/session/{session_id}/message")
    async def send_message(session_id: str, req: MessageReq):
        if store.get_session(session_id) is None:
            raise HTTPException(404, f"Session not found: {session_id}")

        store.emit_event(session_id, Event(
            event_type=EventType.USER_MESSAGE,
            payload={"content": req.message},
        ))

        try:
            running_brain = orchestrator.wake_brain(AGENT_NAME, session_id)
            reply = running_brain.run()
        except Exception as e:
            raise HTTPException(500, f"Brain execution failed: {e}")

        return {"reply": reply, "session_id": session_id}

    return app


def main():
    config = load_config()
    app = create_app(config)
    port = int(config.get("server", {}).get("port", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
