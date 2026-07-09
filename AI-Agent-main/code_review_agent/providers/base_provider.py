from abc import ABC, abstractmethod
from typing import Any

class BaseProviderAdapter(ABC):
    """Abstract interface for LLM provider adapters."""
    
    @abstractmethod
    def invoke(self, input_data: Any, **kwargs: Any) -> Any:
        """Execute synchronous model generation."""
        pass

    @abstractmethod
    async def ainvoke(self, input_data: Any, **kwargs: Any) -> Any:
        """Execute asynchronous model generation."""
        pass
