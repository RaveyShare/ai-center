"""LLM 基础抽象类"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM 配置"""

    model: str
    temperature: float = 0.1
    max_tokens: int = 1000
    top_p: float = 0.9
    api_key: str
    base_url: Optional[str] = None
    timeout: int = 30


class LLMResponse(BaseModel):
    """LLM 响应"""

    content: str
    model: str
    usage: dict[str, int]
    cost_time: int  # 毫秒
    raw_response: Optional[dict[str, Any]] = None


class BaseLLM(ABC):
    """LLM 基础抽象类"""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """验证配置"""
        if not self.config.api_key:
            raise ValueError(f"{self.__class__.__name__} requires api_key")

    @abstractmethod
    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            **kwargs: Any
    ) -> LLMResponse:
        """生成响应

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    async def generate_structured(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            response_format: Optional[dict[str, Any]] = None,
            **kwargs: Any
    ) -> LLMResponse:
        """生成结构化响应（JSON）

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            response_format: 响应格式定义
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查

        Returns:
            是否健康
        """
        pass

    def update_config(self, **kwargs: Any) -> None:
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key) and value is not None:
                setattr(self.config, key, value)