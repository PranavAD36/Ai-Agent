import os
import json
import time
import threading
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils.logger import logger, register_sensitive_token
from utils.metrics import metrics
from providers.factory import ProviderFactory
from providers.base_provider import BaseProviderAdapter

class ProviderManager:
    """Manager to load provider configurations, resolve keys, and orchestrate failover/retries."""
    
    _instance: Optional['ProviderManager'] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._singleton_lock:
            if not cls._instance:
                cls._instance = super(ProviderManager, cls).__new__(cls)
            return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        # Prevent re-initialization in singleton
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self._lock = threading.Lock()
        self.logger = logger
        self.metrics = metrics
        
        # Load configuration
        if not config_path:
            config_path = str(Path(__file__).parent.parent / "config" / "llm_config.json")
            
        self.config_path = config_path
        self.providers: List[Dict[str, Any]] = []
        self.adapters: Dict[str, BaseProviderAdapter] = {}
        
        # Health state
        self.unhealthy_since: Dict[str, float] = {}
        self.fail_count: Dict[str, int] = {}
        
        self.load_config()
        self._initialized = True

    def load_config(self):
        """Load LLM providers configuration from json file."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.providers = data.get("providers", [])
            self.logger.info(f"Loaded {len(self.providers)} LLM providers from configuration.")
            
            # Register sensitive tokens for redaction
            for provider in self.providers:
                api_key = self._resolve_api_key(provider)
                if api_key:
                    register_sensitive_token(api_key)
        except Exception as e:
            self.logger.critical(f"Failed to load LLM configuration from {self.config_path}: {e}")
            self.providers = []

    def _resolve_api_key(self, provider_config: Dict[str, Any]) -> str:
        """Scan environment keys associated with the provider to find a valid key value."""
        env_keys = provider_config.get("env_keys", [])
        for k in env_keys:
            val = os.getenv(k)
            if val and not val.startswith("your_") and val.strip() != "":
                return val.strip()
        return ""

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of active and healthy providers sorted by priority."""
        current_time = time.time()
        available = []
        
        with self._lock:
            for provider in self.providers:
                if not provider.get("enabled", True):
                    continue
                    
                provider_id = provider["id"]
                
                # Check health cooldown
                if provider_id in self.unhealthy_since:
                    unhealthy_time = self.unhealthy_since[provider_id]
                    cooldown = provider.get("cooldown", 60)
                    if current_time - unhealthy_time > cooldown:
                        self.logger.info(f"Cooldown expired for provider '{provider_id}'. Triggering automatic recovery test.")
                        del self.unhealthy_since[provider_id]
                        self.fail_count[provider_id] = 0
                    else:
                        continue
                        
                # Check key availability
                api_key = self._resolve_api_key(provider)
                if not api_key:
                    continue
                    
                available.append(provider)
                
            # Sort by priority ascending (lower value = higher priority)
            available.sort(key=lambda p: p.get("priority", 99))
            return available

    def get_or_create_adapter(self, provider_config: Dict[str, Any]) -> Optional[BaseProviderAdapter]:
        """Instantiate or reuse an adapter for the provider configuration."""
        provider_id = provider_config["id"]
        
        with self._lock:
            if provider_id in self.adapters:
                return self.adapters[provider_id]
                
            name = provider_config["name"]
            api_key = self._resolve_api_key(provider_config)
            model = provider_config["model"]
            timeout = provider_config.get("timeout", 30.0)
            
            try:
                adapter = ProviderFactory.create_provider(
                    name=name,
                    api_key=api_key,
                    model=model,
                    timeout=timeout
                )
                self.adapters[provider_id] = adapter
                return adapter
            except Exception as e:
                self.logger.error(f"Failed to create adapter for provider '{provider_id}': {e}")
                return None

    def get_active_provider_config(self) -> Optional[Dict[str, Any]]:
        """Resolve currently active provider metadata based on priority and health."""
        available = self.get_available_providers()
        return available[0] if available else None

    def mark_unhealthy(self, provider_id: str):
        """Mark provider unhealthy and schedule cooldown."""
        with self._lock:
            self.unhealthy_since[provider_id] = time.time()
            self.fail_count[provider_id] = self.fail_count.get(provider_id, 0) + 1
            self.logger.warning(f"Provider '{provider_id}' marked as UNHEALTHY (fail count: {self.fail_count[provider_id]}).")

    def mark_healthy(self, provider_id: str):
        """Mark provider healthy and reset fail count."""
        with self._lock:
            if provider_id in self.unhealthy_since:
                del self.unhealthy_since[provider_id]
            self.fail_count[provider_id] = 0

    def is_retryable_error(self, error: Exception) -> bool:
        """Differentiate retryable server/rate limit errors from permanent credential/logic errors."""
        err_msg = str(error).lower()
        
        # Permanent errors: fail over immediately to next provider/key
        permanent_keywords = [
            "401", "403", "unauthorized", "invalid api key", "api key not valid",
            "invalid_api_key", "authentication", "forbidden", "permission denied",
            "permission_denied", "billing", "not found", "404", "model_not_found",
            "bad request", "400", "invalid_request_error", "expired", "invalid key"
        ]
        if any(kw in err_msg for kw in permanent_keywords):
            return False
            
        # Retryable errors: rate limits, connection errors, server errors
        retryable_keywords = [
            "429", "rate limit", "too many requests", "resource_exhausted", "resource exhausted",
            "500", "502", "503", "504", "internal server error", "service unavailable",
            "timeout", "deadline", "connection", "network", "remote end closed", "408"
        ]
        if any(kw in err_msg for kw in retryable_keywords):
            return True
            
        # Default to retryable for safety
        return True

    def generate_response(self, input_data: Any, **kwargs: Any) -> Any:
        """Synchronously execute code review prompt with multi-LLM failover."""
        available_providers = self.get_available_providers()
        if not available_providers:
            raise RuntimeError("No LLM providers are currently available or configured with valid API keys.")
            
        last_exception = None
        active_provider_id = self.metrics.active_provider
        
        for provider_config in available_providers:
            provider_id = provider_config["id"]
            
            # Switch logging
            if active_provider_id != "None" and active_provider_id != provider_id:
                self.logger.info(f"SWITCHING LLM PROVIDER: {active_provider_id} -> {provider_id}")
                self.metrics.record_switch(active_provider_id, provider_id)
            active_provider_id = provider_id
            
            adapter = self.get_or_create_adapter(provider_config)
            if not adapter:
                continue
                
            retry_count = provider_config.get("retry_count", 3)
            backoff_factor = provider_config.get("backoff_factor", 2.0)
            backoff_base = provider_config.get("backoff_base", 1.5)
            
            for attempt in range(1, retry_count + 1):
                start_time = time.time()
                try:
                    self.logger.info(f"Routing request to provider '{provider_id}' (attempt {attempt}/{retry_count})")
                    # Synchronous invoke
                    response = adapter.invoke(input_data, **kwargs)
                    
                    # Log success and update metrics
                    latency = time.time() - start_time
                    self.logger.info(f"Request succeeded on provider '{provider_id}'. Latency: {latency:.2f}s")
                    self.metrics.record_success(provider_id, latency, response)
                    self.mark_healthy(provider_id)
                    return response
                    
                except Exception as e:
                    latency = time.time() - start_time
                    self.logger.warning(f"Error on provider '{provider_id}' (attempt {attempt}/{retry_count}): {e}")
                    
                    is_retryable = self.is_retryable_error(e)
                    self.metrics.record_failure(provider_id, e, is_retryable)
                    
                    if is_retryable and attempt < retry_count:
                        sleep_time = backoff_base * (backoff_factor ** (attempt - 1))
                        self.logger.info(f"Retrying on provider '{provider_id}' in {sleep_time:.2f}s...")
                        self.metrics.record_retry(provider_id)
                        time.sleep(sleep_time)
                    else:
                        # Exceeded retries or permanent error on this provider/key. Failover to next key!
                        self.logger.error(f"Provider '{provider_id}' failed. Failing over to the next configured provider.")
                        self.mark_unhealthy(provider_id)
                        last_exception = e
                        break
                        
        self.logger.critical("All configured LLM providers failed to generate a response.")
        self.metrics.record_all_failed()
        raise RuntimeError(f"All LLM providers failed. Last exception: {last_exception}")

    async def agenerate_response(self, input_data: Any, **kwargs: Any) -> Any:
        """Asynchronously execute code review prompt with multi-LLM failover."""
        available_providers = self.get_available_providers()
        if not available_providers:
            raise RuntimeError("No LLM providers are currently available or configured with valid API keys.")
            
        last_exception = None
        active_provider_id = self.metrics.active_provider
        
        for provider_config in available_providers:
            provider_id = provider_config["id"]
            
            # Switch logging
            if active_provider_id != "None" and active_provider_id != provider_id:
                self.logger.info(f"SWITCHING LLM PROVIDER: {active_provider_id} -> {provider_id}")
                self.metrics.record_switch(active_provider_id, provider_id)
            active_provider_id = provider_id
            
            adapter = self.get_or_create_adapter(provider_config)
            if not adapter:
                continue
                
            retry_count = provider_config.get("retry_count", 3)
            backoff_factor = provider_config.get("backoff_factor", 2.0)
            backoff_base = provider_config.get("backoff_base", 1.5)
            
            for attempt in range(1, retry_count + 1):
                start_time = time.time()
                try:
                    self.logger.info(f"Routing async request to provider '{provider_id}' (attempt {attempt}/{retry_count})")
                    # Asynchronous invoke
                    response = await adapter.ainvoke(input_data, **kwargs)
                    
                    latency = time.time() - start_time
                    self.logger.info(f"Async request succeeded on provider '{provider_id}'. Latency: {latency:.2f}s")
                    self.metrics.record_success(provider_id, latency, response)
                    self.mark_healthy(provider_id)
                    return response
                    
                except Exception as e:
                    latency = time.time() - start_time
                    self.logger.warning(f"Async error on provider '{provider_id}' (attempt {attempt}/{retry_count}): {e}")
                    
                    is_retryable = self.is_retryable_error(e)
                    self.metrics.record_failure(provider_id, e, is_retryable)
                    
                    if is_retryable and attempt < retry_count:
                        sleep_time = backoff_base * (backoff_factor ** (attempt - 1))
                        self.logger.info(f"Retrying async on provider '{provider_id}' in {sleep_time:.2f}s...")
                        self.metrics.record_retry(provider_id)
                        await asyncio.sleep(sleep_time)
                    else:
                        self.logger.error(f"Provider '{provider_id}' failed. Failing over to the next configured provider.")
                        self.mark_unhealthy(provider_id)
                        last_exception = e
                        break
                        
        self.logger.critical("All configured LLM providers failed to generate an async response.")
        self.metrics.record_all_failed()
        raise RuntimeError(f"All LLM providers failed. Last exception: {last_exception}")
