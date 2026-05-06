"""Hand 抽象测试。

测试覆盖: LocalHand 执行 / schema 生成 / 错误处理 / as_langchain_tool 转换
"""

import pytest

from ravey.ai.agent_framework.hands.base import Hand
from ravey.ai.agent_framework.hands.local_hand import LocalHand
from ravey.ai.agent_framework.hands.mcp_hand import MCPHand


# ====== 测试用工具函数 ======

def add(a: int, b: int) -> int:
    """两数相加。"""
    return a + b


def greet(name: str) -> str:
    """打招呼。"""
    return f"Hello, {name}!"


def failing_tool(x: str) -> str:
    """总是失败的工具。"""
    raise ValueError(f"模拟错误: {x}")


class TestLocalHand:

    def test_execute(self):
        hand = LocalHand(add)
        result = hand.execute("add", {"a": 1, "b": 2})
        assert result == "3"

    def test_name(self):
        hand = LocalHand(add, zone="green", tags=["math"])
        assert hand.name == "add"
        assert hand.zone == "green"
        assert hand.tags == ["math"]

    def test_schema(self):
        hand = LocalHand(greet)
        schema = hand.schema()
        assert schema["name"] == "greet"
        assert "打招呼" in schema["description"]
        assert "properties" in schema["parameters"]

    def test_execute_error(self):
        hand = LocalHand(failing_tool)
        result = hand.execute("failing_tool", {"x": "test"})
        assert "Error:" in result
        assert "ValueError" in result
        assert "模拟错误" in result

    def test_as_langchain_tool(self):
        hand = LocalHand(add)
        lc_tool = hand.as_langchain_tool()
        assert lc_tool.name == "add"
        result = lc_tool.invoke({"a": 3, "b": 4})
        assert result == 7

    def test_is_hand_subclass(self):
        hand = LocalHand(add)
        assert isinstance(hand, Hand)


class TestMCPHand:

    def test_name(self):
        hand = MCPHand("send_text", "http://localhost:8080/mcp")
        assert hand.name == "send_text"

    def test_schema_fallback(self):
        """无法连接 MCP 时返回默认 schema。"""
        hand = MCPHand("send_text", "http://127.0.0.1:59999/mcp")
        schema = hand.schema()
        assert schema["name"] == "send_text"
        assert "MCP tool" in schema["description"]

    def test_execute_connection_error(self):
        """无法连接 MCP 时返回错误信息。"""
        hand = MCPHand("send_text", "http://127.0.0.1:59999/mcp")
        result = hand.execute("send_text", {"text": "hello"})
        assert "MCP Error" in result

    def test_is_hand_subclass(self):
        hand = MCPHand("test", "http://localhost:8080/mcp")
        assert isinstance(hand, Hand)
