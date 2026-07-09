from typing import Any, List, Optional
from pydantic import PrivateAttr
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun
from services.provider_manager import ProviderManager

class FailoverChatModel(BaseChatModel):
    """LangChain-compatible chat model providing seamless failover and smart retries."""
    
    temperature: float = 0.1
    _provider_manager: ProviderManager = PrivateAttr()

    def __init__(self, provider_manager: Optional[ProviderManager] = None, **kwargs: Any):
        super().__init__(**kwargs)
        self._provider_manager = provider_manager or ProviderManager()

    @property
    def _llm_type(self) -> str:
        return "failover-chat-model"

    @property
    def model_name(self) -> str:
        """Retrieve the model name from the currently active healthy provider."""
        active = self._provider_manager.get_active_provider_config()
        return active["model"] if active else "unknown"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        if "temperature" not in kwargs:
            kwargs["temperature"] = self.temperature
        response_msg = self._provider_manager.generate_response(messages, stop=stop, **kwargs)
        return ChatResult(generations=[ChatGeneration(message=response_msg)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any
    ) -> ChatResult:
        if "temperature" not in kwargs:
            kwargs["temperature"] = self.temperature
        response_msg = await self._provider_manager.agenerate_response(messages, stop=stop, **kwargs)
        return ChatResult(generations=[ChatGeneration(message=response_msg)])
