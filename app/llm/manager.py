"""
LLM Manager coordinating dynamic selection of available cloud and local providers.
"""
import os
from typing import Optional, Any
from app.config.settings import settings
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse
from app.llm.gemini import GeminiProvider
from app.llm.openrouter import OpenRouterProvider
from app.llm.llama_cpp import LlamaCppProvider
from app.llm.ollama import OllamaProvider
from app.llm.local_engine import LocalEngineProvider

logger = get_logger("llm_manager")


class LLMManager:
    """Coordinates intelligent routing between zero-cost cloud and lightweight local engines."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {
            "gemini": GeminiProvider(),
            "openrouter": OpenRouterProvider(),
            "ollama": OllamaProvider(host=settings.ollama_host, model_name=settings.ollama_model),
            "llama_cpp": LlamaCppProvider(),
            "local_engine": LocalEngineProvider(),
        }

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Fetch preferred provider or auto-select best available zero-cost provider."""
        target_name = (name or settings.model_provider).lower()

        if target_name in ["auto", "", "default"]:
            # Auto-selection priority:
            # 1. Google Gemini Free Tier (Fastest, smart, 0MB RAM)
            if self._providers["gemini"].is_available():
                return self._providers["gemini"]
            # 2. OpenRouter Free Tier (0MB RAM)
            if self._providers["openrouter"].is_available():
                return self._providers["openrouter"]
            # 3. Lightweight Local Ollama (Offline fallback)
            if self._providers["ollama"].is_available():
                return self._providers["ollama"]
            # 4. Local rule-based engine (Zero dependency)
            return self._providers["local_engine"]

        provider = self._providers.get(target_name)
        if provider and provider.is_available():
            return provider

        if target_name in ["llama_cpp", "local_engine"]:
            return self._providers["local_engine"]

        logger.debug(f"Provider '{target_name}' is not currently available. Falling back to auto.")
        return self.get_provider("auto")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Route generation request to active provider with graceful fallback."""
        provider = self.get_provider(provider_name)
        try:
            return provider.generate(prompt, system_prompt=system_prompt, **kwargs)
        except Exception as ex:
            logger.warning(f"Provider '{provider.get_model_info().get('provider')}' failed: {ex}. Falling back to local_engine.")
            # Fallback to local_engine on connection failure
            fallback = self._providers["local_engine"]
            return fallback.generate(prompt, system_prompt=system_prompt, **kwargs)

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs
    ):
        """Route streaming generation request to active provider with progressive token delivery."""
        provider = self.get_provider(provider_name)
        if hasattr(provider, "stream_generate"):
            try:
                for chunk in provider.stream_generate(prompt, system_prompt=system_prompt, **kwargs):
                    yield chunk
                return
            except Exception as ex:
                logger.warning(f"Streaming failed on {provider.get_model_info().get('provider')}: {ex}. Falling back.")

        # Fallback to standard generate
        resp = self.generate(prompt=prompt, system_prompt=system_prompt, provider_name=provider_name, **kwargs)
        if resp.content:
            yield resp.content

    def is_real_llm_active(self) -> bool:
        """Returns True if a real generative LLM (Gemini, OpenRouter, Ollama) is active."""
        active = self.get_provider()
        return active.get_model_info().get("provider") in ["gemini", "openrouter", "ollama"]

    def get_status(self) -> dict[str, Any]:
        """Diagnostic summary of all LLM providers."""
        active = self.get_provider()
        return {
            "configured_provider": settings.model_provider,
            "active_provider": active.get_model_info().get("provider"),
            "is_real_llm": self.is_real_llm_active(),
            "providers_status": {
                name: p.get_model_info() for name, p in self._providers.items()
            }
        }


llm_manager = LLMManager()
