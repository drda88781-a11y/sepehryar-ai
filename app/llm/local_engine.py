"""
Local Intelligence Operations Engine for Sepehryar ERP.
Provides high-speed, zero-dependency, deterministic natural language interpretation
and Persian response synthesis for accounting, SQL queries, and diagnostics.
"""
import re
import time
from typing import Optional, Any
from app.llm.base import LLMProvider, LLMResponse


class LocalEngineProvider(LLMProvider):
    """Deterministic local AI engine specialized in Sepehryar accounting and SQL schemas."""

    def is_available(self) -> bool:
        return True

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
        clean = prompt.strip()

        # Generate intelligent Persian response based on semantic intent
        answer = self._synthesize_response(clean)
        duration = (time.perf_counter() - start) * 1000

        return LLMResponse(
            content=answer,
            model_name="Sepehryar-Local-Engine-v1",
            tokens_used=len(answer.split()),
            duration_ms=round(duration, 2),
            provider="local_engine"
        )

    def _synthesize_response(self, query: str) -> str:
        from app.agent.cognitive_engine import cognitive_engine
        # Extract user query if wrapped in prompt template
        match = re.search(r"پرسش(?:\s+یا\s+پیام\s+فعلی)?\s+کاربر:\s*«([\s\S]*?)»", query)
        actual_query = match.group(1).strip() if match else query
        cog_res = cognitive_engine.reason_and_solve(actual_query)
        return cog_res.to_formatted_markdown()

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "local_engine",
            "model_name": "Sepehryar-Local-Engine-v1",
            "is_available": True,
            "latency": "sub-millisecond",
            "offline": True
        }
