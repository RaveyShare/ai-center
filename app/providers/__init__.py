from .base import Provider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .mock_provider import MockProvider

def get_provider(name: str) -> Provider:
    if name == "openai":
        return OpenAIProvider()
    if name == "anthropic":
        return AnthropicProvider()
    if name == "mock":
        return MockProvider()
    raise ValueError("Unsupported provider")
