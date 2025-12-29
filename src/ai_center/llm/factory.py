"""LLM 工厂类"""
from typing import Optional

from ..config import Settings
from .base import BaseLLM, LLMConfig
from .qwen import QwenLLM


class LLMFactory:
    """LLM 工厂"""

    _instances: dict[str, BaseLLM] = {}

    @classmethod
    def create(
            cls,
            provider: str,
            settings: Settings,
            model: Optional[str] = None
    ) -> BaseLLM:
        """创建或获取 LLM 实例

        Args:
            provider: 提供商（qwen/openai/claude）
            settings: 配置对象
            model: 指定模型（可选）

        Returns:
            LLM 实例
        """
        # 使用 provider 作为缓存 key
        cache_key = f"{provider}:{model or 'default'}"

        if cache_key in cls._instances:
            return cls._instances[cache_key]

        # 根据 provider 创建对应实例
        if provider == "qwen":
            config = LLMConfig(
                model=model or settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.dashscope_api_key
            )
            instance = QwenLLM(config)

        elif provider == "openai":
            # 预留 OpenAI 实现
            config = LLMConfig(
                model=model or "gpt-4",
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            # instance = OpenAILLM(config)
            raise NotImplementedError("OpenAI provider not implemented yet")

        elif provider == "claude":
            # 预留 Claude 实现
            raise NotImplementedError("Claude provider not implemented yet")

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        # 缓存实例
        cls._instances[cache_key] = instance
        return instance

    @classmethod
    def get_default(cls, settings: Settings) -> BaseLLM:
        """获取默认 LLM 实例"""
        return cls.create(
            provider=settings.llm_provider,
            settings=settings
        )

    @classmethod
    def clear_cache(cls) -> None:
        """清除缓存"""
        cls._instances.clear()