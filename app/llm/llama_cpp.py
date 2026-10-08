"""
Llama.cpp provider for loading GGUF format weights locally on Windows CPU/GPU.
"""
import time
from pathlib import Path
from typing import Optional, Any
from app.config.settings import settings, BASE_DIR
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse

logger = get_logger("llama_cpp")


class LlamaCppProvider(LLMProvider):
    """Integrates llama-cpp-python runtime for offline GGUF model execution."""

    def __init__(self) -> None:
        self.model_path = Path(settings.model_path)
        if not self.model_path.is_absolute():
            self.model_path = BASE_DIR / self.model_path
        self._llm_instance = None
        self._initialized = False

    def is_available(self) -> bool:
        """Verify model weights exist on disk."""
        return self.model_path.exists() and self.model_path.is_file()

    def _ensure_loaded(self) -> None:
        """Load GGUF weights into memory."""
        if self._initialized:
            return

        if not self.is_available():
            raise FileNotFoundError(
                f"فایل مدل محلی GGUF در مسیر '{self.model_path}' یافت نشد. "
                "لطفاً وزن‌های مدل را در پوشه models/ قرار داده یا از Local Engine استفاده فرمایید."
            )

        try:
            from llama_cpp import Llama  # Lazy import
            logger.info(f"Loading GGUF model from {self.model_path} (n_ctx={settings.model_context_size})...")
            self._llm_instance = Llama(
                model_path=str(self.model_path),
                n_ctx=settings.model_context_size,
                n_gpu_layers=settings.model_gpu_layers,
                verbose=settings.debug
            )
            self._initialized = True
            logger.info("GGUF model loaded successfully.")
        except ImportError:
            raise RuntimeError("کتابخانه llama-cpp-python بر روی سیستم نصب نیست.")
        except Exception as e:
            logger.error(f"Failed to load GGUF model: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
        stop: Optional[list[str]] = None,
        **kwargs
    ) -> LLMResponse:
        self._ensure_loaded()
        start = time.perf_counter()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        output = self._llm_instance(
            full_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop or ["<|im_end|>", "User:", "کاربر:"],
        )

        duration = (time.perf_counter() - start) * 1000
        text = output["choices"][0]["text"].strip()
        tokens = output.get("usage", {}).get("total_tokens", 0)

        return LLMResponse(
            content=text,
            model_name=self.model_path.name,
            tokens_used=tokens,
            duration_ms=round(duration, 2),
            provider="llama_cpp"
        )

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "llama_cpp",
            "model_path": str(self.model_path),
            "file_exists": self.is_available(),
            "context_size": settings.model_context_size,
            "gpu_layers": settings.model_gpu_layers,
            "is_loaded": self._initialized
        }
