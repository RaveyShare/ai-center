"""TaskPlannerAgent 装配测试。

覆盖：
  - make_brain_config 构造正确
  - build_brain 注入了 5 个 Hand
  - extra_hands 合并不丢
  - SYSTEM_PROMPT 包含工具名
"""

import pytest

from ravey.ai.agent_framework.brain import Brain, BrainConfig
from ravey.ai.agent_framework.hands import LocalHand
from ravey.ai.agent_framework.session import MySQLSessionStore

from ravey.ai.tasks.agent import (
    AGENT_NAME,
    SYSTEM_PROMPT,
    build_brain,
    make_brain_config,
)


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


class TestMakeBrainConfig:

    def test_default_values(self):
        cfg = make_brain_config()
        assert cfg.agent_name == AGENT_NAME
        assert cfg.system_prompt == SYSTEM_PROMPT
        assert cfg.llm_provider == "dashscope"
        assert cfg.llm_model == "qwen-plus"
        assert cfg.max_tool_calls == 30

    def test_custom_overrides(self):
        cfg = make_brain_config(
            llm_provider="openai",
            llm_model="gpt-4o",
            max_tool_calls=5,
        )
        assert cfg.llm_provider == "openai"
        assert cfg.llm_model == "gpt-4o"
        assert cfg.max_tool_calls == 5


class TestBuildBrain:

    def test_brain_is_instance(self, store):
        brain = build_brain(store)
        assert isinstance(brain, Brain)

    def test_brain_config_wired(self, store):
        brain = build_brain(store, llm_provider="dashscope", llm_model="qwen-turbo")
        assert isinstance(brain.config, BrainConfig)
        assert brain.config.agent_name == AGENT_NAME
        assert brain.config.llm_model == "qwen-turbo"

    def test_brain_has_five_hands(self, store):
        brain = build_brain(store)
        assert set(brain.hands.keys()) == {
            "parse_requirement", "split_task", "estimate_effort",
            "schedule_tasks", "save_task_tree",
        }

    def test_extra_hands_merged(self, store):
        def echo(msg: str) -> str:
            """Echo back."""
            return msg

        extra = {"echo": LocalHand(echo)}
        brain = build_brain(store, extra_hands=extra)
        assert "echo" in brain.hands
        assert "parse_requirement" in brain.hands
        assert len(brain.hands) == 6

    def test_brain_session_store_wired(self, store):
        brain = build_brain(store)
        assert brain.session_store is store


class TestSystemPrompt:

    def test_mentions_all_tools(self):
        for tool_name in (
            "parse_requirement",
            "split_task",
            "estimate_effort",
            "schedule_tasks",
            "save_task_tree",
        ):
            assert tool_name in SYSTEM_PROMPT, f"prompt missing {tool_name}"

    def test_has_workflow_guidance(self):
        assert "工作流程" in SYSTEM_PROMPT
        assert "注意事项" in SYSTEM_PROMPT
