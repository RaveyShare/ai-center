"""LocalHand — 本地函数工具。

在 Brain 进程内直接执行。适用于轻量级、无副作用的操作。
保留 v2 的 @agent_tool 用法，内部包装为 LocalHand。
"""

from typing import Any, Callable

from langchain_core.tools import BaseTool
from langchain_core.tools import tool as langchain_tool

from ravey.ai.agent_framework.hands.base import Hand


class LocalHand(Hand):

    def __init__(self, func: Callable, zone: str = "green", tags: list[str] | None = None):
        self._func = func
        self._name = func.__name__
        self._zone = zone
        self._tags = tags or []
        self._lc_tool: BaseTool = langchain_tool(func)

    @property
    def name(self) -> str:
        return self._name

    @property
    def zone(self) -> str:
        return self._zone

    @property
    def tags(self) -> list[str]:
        return self._tags

    def execute(self, name: str, input: dict[str, Any]) -> str:
        try:
            result = self._func(**input)
            return str(result)
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"

    def schema(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._lc_tool.description,
            "parameters": self._lc_tool.args_schema.model_json_schema() if self._lc_tool.args_schema else {},
        }

    def as_langchain_tool(self) -> BaseTool:
        return self._lc_tool
