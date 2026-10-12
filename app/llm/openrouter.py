"""
Free Cloud OpenRouter Provider (Zero local RAM / CPU footprint).
Connects to OpenRouter.ai Free Tier models via REST API using pure Python standard library.
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Any
from app.config.settings import settings
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse

logger = get_logger("openrouter")


class OpenRouterProvider(LLMProvider):
    """
    Ultra-flexible zero-load provider supporting free high-tier open models.
    (e.g., deepseek/deepseek-r1:free, meta-llama/llama-3.3-70b-instruct:free).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> None:
        self.api_key = (api_key or settings.openrouter_api_key or "").strip()
        self.model_name = model_name or settings.openrouter_model or "deepseek/deepseek-r1:free"

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.2,
        stop: Optional[list[str]] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("OpenRouter API key is not configured. Add OPENROUTER_API_KEY to .env")

        start = time.perf_counter()
        url = "https://openrouter.ai/api/v1/chat/completions"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stop:
            payload["stop"] = stop

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://sepehryar.local",
                "X-Title": "Sepehryar AI Engine",
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=35.0) as resp:
                resp_json = json.loads(resp.read().decode("utf-8"))

            choices = resp_json.get("choices", [])
            content = ""
            if choices:
                content = choices[0].get("message", {}).get("content", "").strip()

            duration = (time.perf_counter() - start) * 1000
            tokens_used = resp_json.get("usage", {}).get("total_tokens", len(content.split()))

            return LLMResponse(
                content=content,
                model_name=self.model_name,
                tokens_used=tokens_used,
                duration_ms=round(duration, 2),
                provider="openrouter"
            )

        except urllib.error.HTTPError as ex:
            err_body = ex.read().decode("utf-8") if ex.fp else str(ex)
            logger.error(f"OpenRouter API HTTP Error {ex.code}: {err_body}")
            raise RuntimeError(f"خطای سرویس OpenRouter ({ex.code}): {err_body}") from ex
        except Exception as ex:
            logger.error(f"OpenRouter API request failed: {ex}")
            raise RuntimeError(f"ارتباط با OpenRouter برقرار نشد: {ex}") from ex

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "openrouter",
            "model_name": self.model_name,
            "is_available": self.is_available(),
            "cloud_free": True,
            "local_load": "0% CPU / 0MB RAM"
        }
