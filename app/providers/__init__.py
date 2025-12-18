from .base import Provider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .compatible_provider import CompatibleProvider
from .mock_provider import MockProvider

def get_provider(name: str) -> Provider:
    if name == "openai":
        return OpenAIProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "compatible" or name in ["deepseek", "qwen", "kimi"]:
        return CompatibleProvider()
    if name == "mock":
        return MockProvider()
    raise ValueError(f"Unsupported provider: {name}")
