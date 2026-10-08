"""
Abstract base class and data models for local LLM providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    content: str = Field(description="پاسخ متنی مدل به زبان فارسی یا داده ساختاریافته")
    model_name: str
    tokens_used: int = 0
    duration_ms: float = 0.0
    provider: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    """Abstract interface that all local model providers must implement."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Optional[list[str]] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response text from local model."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if runtime and model weights are ready and loaded."""
        pass

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Return diagnostic metadata about current model configuration."""
        pass
