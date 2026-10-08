"""
LLM Manager coordinating dynamic selection of available local providers.
"""
from typing import Optional, Any
from app.config.settings import settings
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse
from app.llm.llama_cpp import LlamaCppProvider
from app.llm.ollama import OllamaProvider
from app.llm.local_engine import LocalEngineProvider

logger = get_logger("llm_manager")


class LLMManager:
    """Coordinates local model execution, fallback, and status reporting."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProvider] = {
            "local_engine": LocalEngineProvider(),
            "llama_cpp": LlamaCppProvider(),
            "ollama": OllamaProvider(),
        }

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Fetch preferred provider or fallback to available one."""
        target_name = (name or settings.model_provider).lower()
        provider = self._providers.get(target_name)

        if provider and provider.is_available():
            return provider

        # If configured provider is unavailable (e.g. gguf file not placed yet), fallback to local_engine
        logger.debug(f"Provider '{target_name}' is not currently available. Falling back to local_engine.")
        return self._providers["local_engine"]

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Route generation request to active provider."""
        provider = self.get_provider(provider_name)
        return provider.generate(prompt, system_prompt=system_prompt, **kwargs)

    def get_status(self) -> dict[str, Any]:
        """Diagnostic summary of all LLM providers."""
        active = self.get_provider()
        return {
            "configured_provider": settings.model_provider,
            "active_provider": active.get_model_info().get("provider"),
            "providers_status": {
                name: p.get_model_info() for name, p in self._providers.items()
            }
        }


llm_manager = LLMManager()
