"""Hand 协议 — 统一的工具执行接口。

核心思想（Managed Agents）：
Brain 不关心 Hand 的实现细节。
execute(name, input) → string，Brain 只知道这一个接口。

Hand 的职责：
1. 接收 Brain 的工具调用请求
2. 执行实际操作（本地函数 / MCP 调用 / 沙箱代码执行）
3. 返回字符串结果

Hand 不应该：
1. 持有 Brain 的引用
2. 直接操作 Session
3. 知道自己被哪个 Brain 调用
"""

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.tools import BaseTool


class Hand(ABC):
    """Hand 基类。所有工具执行器都实现此接口。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称（LLM function calling 用这个名字引用）。"""
        ...

    @abstractmethod
    def execute(self, name: str, input: dict[str, Any]) -> str:
        """执行工具调用，返回字符串结果。

        Args:
            name: 工具名称（通常等于 self.name，但 Brain 传入的）
            input: LLM 生成的参数 dict

        Returns:
            工具执行结果的字符串表示

        Raises:
            任何异常都应被 Brain 捕获并记录为 ERROR 事件
        """
        ...

    @abstractmethod
    def schema(self) -> dict[str, Any]:
        """返回工具的 JSON Schema（供 LLM function calling）。

        格式遵循 OpenAI function calling schema:
        {
            "name": "tool_name",
            "description": "...",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        ...

    def as_langchain_tool(self) -> BaseTool:
        """转为 LangChain BaseTool（兼容 v2 的 LangGraph 工具注入）。

        默认实现：包装 execute 方法。子类可覆盖。
        """
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            func=lambda **kwargs: self.execute(self.name, kwargs),
            name=self.name,
            description=self.schema().get("description", ""),
        )
