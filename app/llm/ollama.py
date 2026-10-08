"""
Local Ollama provider connecting to on-premise Ollama instance via loopback.
"""
import json
import time
import urllib.request
from typing import Optional, Any
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse

logger = get_logger("ollama")


class OllamaProvider(LLMProvider):
    """Integrates with local Ollama runtime over 127.0.0.1 loopback."""

    def __init__(self, host: str = "http://127.0.0.1:11434", model_name: str = "qwen2.5:7b") -> None:
        self.host = host
        self.model_name = model_name

    def is_available(self) -> bool:
        """Check if local Ollama daemon is reachable on 127.0.0.1."""
        try:
            req = urllib.request.Request(f"{self.host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Optional[list[str]] = None,
        **kwargs
    ) -> LLMResponse:
        start = time.perf_counter()
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "stop": stop or []
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        duration = (time.perf_counter() - start) * 1000
        content = body.get("response", "").strip()

        return LLMResponse(
            content=content,
            model_name=self.model_name,
            duration_ms=round(duration, 2),
            provider="ollama"
        )

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "ollama",
            "host": self.host,
            "model_name": self.model_name,
            "is_available": self.is_available()
        }
