from typing import Dict, Type, Any
from providers.base_provider import BaseProviderAdapter
from providers.gemini_provider import GeminiProviderAdapter
from providers.groq_provider import GroqProviderAdapter

class ProviderFactory:
    """Factory to register and instantiate provider adapters dynamically."""
    
    _registry: Dict[str, Type[BaseProviderAdapter]] = {
        "gemini": GeminiProviderAdapter,
        "groq": GroqProviderAdapter
    }

    @classmethod
    def register_provider(cls, name: str, adapter_cls: Type[BaseProviderAdapter]):
        """Register a new LLM provider adapter."""
        cls._registry[name.lower()] = adapter_cls

    @classmethod
    def create_provider(cls, name: str, api_key: str, model: str, **kwargs: Any) -> BaseProviderAdapter:
        """Create and initialize a registered LLM provider adapter."""
        name_lower = name.lower()
        if name_lower not in cls._registry:
            raise ValueError(f"Unknown provider name: {name}")
        return cls._registry[name_lower](api_key=api_key, model=model, **kwargs)
