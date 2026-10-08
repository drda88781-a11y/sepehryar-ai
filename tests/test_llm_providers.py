"""
Tests for local LLM providers and LLM manager fallback mechanisms.
"""
from app.llm.local_engine import LocalEngineProvider
from app.llm.llama_cpp import LlamaCppProvider
from app.llm.manager import llm_manager


def test_local_engine_provider():
    """Verify built-in local engine provides immediate Persian responses."""
    engine = LocalEngineProvider()
    assert engine.is_available() is True

    res = engine.generate("تعداد کالاها چقدره؟")
    assert res.content is not None
    assert "TblKala" in res.content
    assert res.provider == "local_engine"
    assert res.duration_ms >= 0.0


def test_llama_cpp_availability_handling():
    """Verify LlamaCppProvider safely indicates availability without crashing."""
    provider = LlamaCppProvider()
    info = provider.get_model_info()
    assert info["provider"] == "llama_cpp"
    assert "file_exists" in info


def test_llm_manager_fallback():
    """Verify LLMManager falls back to LocalEngine when model weights are not loaded."""
    active = llm_manager.get_provider("llama_cpp")
    assert active.is_available() is True
    # It safely falls back to local_engine if GGUF is not present
    assert active.get_model_info()["provider"] in ("local_engine", "llama_cpp")

    response = llm_manager.generate("ارتباط TblKala با TR چیه؟")
    assert response is not None
    assert len(response.content) > 0
