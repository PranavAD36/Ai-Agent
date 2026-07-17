from typing import Dict, Type, Any
from providers.base_provider import BaseProviderAdapter

class ProviderFactory:
    """Factory to register and instantiate provider adapters dynamically."""
    
    _registry: Dict[str, Type[BaseProviderAdapter]] = {}

    @classmethod
    def _initialize_registry(cls):
        if cls._registry:
            return
            
        # Dynamically register Gemini provider
        try:
            from providers.gemini_provider import GeminiProviderAdapter
            cls._registry["gemini"] = GeminiProviderAdapter
        except ImportError as e:
            print(f"[*] Warning: Gemini provider adapter not registered: {e}")
            
        # Dynamically register Groq provider
        try:
            from providers.groq_provider import GroqProviderAdapter
            cls._registry["groq"] = GroqProviderAdapter
        except ImportError as e:
            print(f"[*] Warning: Groq provider adapter not registered: {e}")

    @classmethod
    def register_provider(cls, name: str, adapter_cls: Type[BaseProviderAdapter]):
        """Register a new LLM provider adapter."""
        cls._initialize_registry()
        cls._registry[name.lower()] = adapter_cls

    @classmethod
    def create_provider(cls, name: str, api_key: str, model: str, **kwargs: Any) -> BaseProviderAdapter:
        """Create and initialize a registered LLM provider adapter."""
        cls._initialize_registry()
        name_lower = name.lower()
        if name_lower not in cls._registry:
            raise ValueError(
                f"Unknown or unavailable provider name: {name}. "
                f"Please ensure any required adapter package (like langchain-groq or langchain-google-genai) is installed."
            )
        return cls._registry[name_lower](api_key=api_key, model=model, **kwargs)
