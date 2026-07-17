from typing import Optional
from services.failover_llm import FailoverChatModel
from services.provider_manager import ProviderManager

def get_llm(temperature: float = 0.1) -> Optional[FailoverChatModel]:
    """Helper to return the unified FailoverChatModel drop-in replacement, or None if no keys configured."""
    pm = ProviderManager()
    if not pm.get_available_providers():
        return None
    return FailoverChatModel(provider_manager=pm, temperature=temperature)
