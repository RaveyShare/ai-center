"""多 provider LLM 工厂。

把"按 provider 名称取 LLM 实例"的细节集中在一处：
  - `_PROVIDER_TEMPLATES` 维护各家厂商的默认 base_url 与默认/快速模型，
    业务通过 `agent_config.yaml` 只需写 api_key 即可，模板做合并。
  - `LLMFactory` 是无状态对象，构造一次即可在整个应用生命周期复用。
"""

from __future__ import annotations

from langchain_openai import ChatOpenAI


# 预置 provider 配置模板：default_url + 默认模型 + 快速模型
_PROVIDER_TEMPLATES = {
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "fast_model": "qwen-turbo",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "fast_model": "gpt-4o-mini",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "fast_model": "deepseek-chat",
    },
    "volcengine": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "default_model": "doubao-pro-32k",
        "fast_model": "doubao-lite-32k",
    },
}


class LLMFactory:
    """LLM 工厂，从配置创建 LLM 实例。

    Usage:
        factory = LLMFactory(providers_config)
        llm = factory.create("dashscope")              # 默认模型
        llm = factory.create("dashscope", "qwen-max")  # 指定模型
        llm = factory.fast("dashscope")                # 快速模型
    """

    def __init__(self, providers: dict):
        """
        Args:
            providers: 从 YAML 配置解析的 provider 字典
                {
                    "dashscope": {"api_key": "sk-xxx", "base_url": "...", "default_model": "..."},
                    ...
                }
        """
        self._providers: dict[str, dict] = {}
        for name, conf in providers.items():
            template = _PROVIDER_TEMPLATES.get(name, {})
            self._providers[name] = {**template, **conf}

    def create(
        self,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> ChatOpenAI:
        """创建 LLM 实例。"""
        provider = provider or self._default_provider
        conf = self._providers.get(provider)
        if not conf:
            raise ValueError(
                f"Unknown provider: {provider}. Available: {list(self._providers.keys())}"
            )

        return ChatOpenAI(
            api_key=conf.get("api_key", ""),
            base_url=conf.get("base_url", ""),
            model=model or conf.get("default_model", ""),
            temperature=temperature,
            **kwargs,
        )

    def fast(self, provider: str | None = None, **kwargs) -> ChatOpenAI:
        """创建快速 LLM（小模型，省 token）。"""
        provider = provider or self._default_provider
        conf = self._providers.get(provider, {})
        return self.create(provider, model=conf.get("fast_model"), **kwargs)

    @property
    def _default_provider(self) -> str:
        return next(iter(self._providers))
