"""
Free Cloud Google Gemini Provider (Zero local RAM / CPU footprint).
Connects to Google Generative Language REST API.
Includes resilient proxy handling (SOCKS5 / HTTP) and automatic model fallback.
"""
import json
import time
import socket
import http.client
import urllib.request
import urllib.error
from typing import Optional, Any
from app.config.settings import settings
from app.core.logger import get_logger
from app.llm.base import LLMProvider, LLMResponse

logger = get_logger("gemini")

# Optional PySocks import for proxy routing
try:
    import socks
    HAS_PYSOCKS = True
except ImportError:
    HAS_PYSOCKS = False

FALLBACK_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.1-pro-preview",
]


class SocksiPyConnection(http.client.HTTPSConnection):
    """HTTPS connection routed through local SOCKS5 proxy without altering global sockets."""
    def __init__(self, host, port=443, proxy_host="127.0.0.1", proxy_port=10808, **kwargs):
        super().__init__(host, port, **kwargs)
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def connect(self):
        if not HAS_PYSOCKS:
            return super().connect()
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, self.proxy_host, self.proxy_port)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


class SocksiPyHandler(urllib.request.HTTPSHandler):
    """Urllib handler for SOCKS5 tunneling."""
    def __init__(self, proxy_host="127.0.0.1", proxy_port=10808):
        super().__init__()
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port

    def https_open(self, req):
        return self.do_open(
            lambda host, **kw: SocksiPyConnection(host, proxy_host=self.proxy_host, proxy_port=self.proxy_port, **kw),
            req
        )


class GeminiProvider(LLMProvider):
    """
    Ultra-fast, zero-load provider using Google's Free Tier Gemini models.
    Consumes 0MB local RAM and 0% GPU.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> None:
        self.api_key = (api_key or settings.gemini_api_key or "").strip()
        raw_model = (model_name or settings.gemini_model or "gemini-flash-latest").strip()
        if raw_model.startswith("models/"):
            raw_model = raw_model.replace("models/", "")
            
        self.model_name = raw_model
        self._cached_openers: Optional[list[urllib.request.OpenerDirector]] = None
        self._last_opener_check: float = 0.0

    def is_available(self) -> bool:
        """Available if a valid API key is present."""
        return bool(self.api_key and len(self.api_key) > 10)

    def _is_port_open(self, host: str, port: int, timeout: float = 0.05) -> bool:
        """Check if a local proxy port is open with ultra-fast timeout (50ms)."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, socket.timeout):
            return False

    def _get_openers(self, force_refresh: bool = False) -> list[urllib.request.OpenerDirector]:
        """
        Build prioritized list of openers (Proxy-aware for Iran + Direct fallback).
        Cached for 180 seconds to eliminate dead port probing delay on every request.
        """
        now = time.time()
        if not force_refresh and self._cached_openers is not None and (now - self._last_opener_check) < 180.0:
            return self._cached_openers

        openers: list[urllib.request.OpenerDirector] = []
        # 1. Direct connection first (ultra-fast <1s if Google API reachable directly or via transparent VPN/WARP)
        openers.append(urllib.request.build_opener())

        # 2. SOCKS5 Proxy (V2Ray default 10808)
        if HAS_PYSOCKS and self._is_port_open("127.0.0.1", 10808, timeout=0.05):
            openers.append(urllib.request.build_opener(SocksiPyHandler("127.0.0.1", 10808)))

        # 3. HTTP Proxy (V2Ray 10809 or Clash 7890)
        for port in (10809, 7890):
            if self._is_port_open("127.0.0.1", port, timeout=0.05):
                handler = urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{port}",
                    "https": f"http://127.0.0.1:{port}"
                })
                openers.append(urllib.request.build_opener(handler))

        self._cached_openers = openers
        self._last_opener_check = now
        return openers

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        stop: Optional[list[str]] = None,
        **kwargs
    ) -> LLMResponse:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured. Add GEMINI_API_KEY to .env")

        start = time.perf_counter()

        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        if stop:
            payload["generationConfig"]["stopSequences"] = stop

        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        openers = self._get_openers()

        # Models to try: primary model first, followed by fallbacks
        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]

        last_error = None
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )

            for idx, opener in enumerate(openers):
                try:
                    with opener.open(req, timeout=12.0) as resp:
                        resp_json = json.loads(resp.read().decode("utf-8"))

                    candidates = resp_json.get("candidates", [])
                    content = ""
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        content = "".join([p.get("text", "") for p in parts]).strip()

                    duration = (time.perf_counter() - start) * 1000
                    tokens_used = resp_json.get("usageMetadata", {}).get("totalTokenCount", len(content.split()))

                    # Promote successful opener to index 0 for future calls
                    if idx > 0 and self._cached_openers:
                        self._cached_openers.insert(0, self._cached_openers.pop(idx))

                    return LLMResponse(
                        content=content,
                        model_name=model,
                        tokens_used=tokens_used,
                        duration_ms=round(duration, 2),
                        provider="gemini"
                    )

                except urllib.error.HTTPError as ex:
                    err_body = ex.read().decode("utf-8") if ex.fp else str(ex)
                    logger.warning(f"Gemini API model {model} HTTP Error {ex.code}: {err_body}")
                    # If 404 (model deprecated) or 429 (quota), try next model
                    if ex.code in (404, 429, 503):
                        last_error = RuntimeError(f"خطای سرویس Gemini ({ex.code}): {err_body}")
                        break
                    last_error = RuntimeError(f"خطای سرویس Gemini ({ex.code}): {err_body}")
                except Exception as ex:
                    logger.warning(f"Gemini opener failed for {model}: {ex}")
                    last_error = ex
                    continue

        raise RuntimeError(f"ارتباط با Gemini برقرار نشد: {last_error}")

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.2,
        **kwargs
    ):
        """
        Stream output tokens progressively using Gemini streamGenerateContent SSE endpoint.
        Yields text chunks as they arrive from the Google Generative Language API.
        """
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        openers = self._get_openers()
        models_to_try = [self.model_name] + [m for m in FALLBACK_MODELS if m != self.model_name]

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={self.api_key}"
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json; charset=utf-8"},
                method="POST"
            )

            for idx, opener in enumerate(openers):
                try:
                    with opener.open(req, timeout=15.0) as resp:
                        for line in resp:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                json_part = line_str[6:].strip()
                                if not json_part:
                                    continue
                                try:
                                    data = json.loads(json_part)
                                    candidates = data.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        chunk_text = "".join([p.get("text", "") for p in parts if "text" in p])
                                        if chunk_text:
                                            yield chunk_text
                                except Exception:
                                    pass

                    # Promote working opener
                    if idx > 0 and self._cached_openers:
                        self._cached_openers.insert(0, self._cached_openers.pop(idx))
                    return

                except Exception as ex:
                    logger.debug(f"Streaming failed with opener on {model}: {ex}")
                    continue

        # If streaming failed completely, fallback to single generate
        full_resp = self.generate(prompt=prompt, system_prompt=system_prompt, max_tokens=max_tokens, temperature=temperature)
        if full_resp.content:
            yield full_resp.content

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "gemini",
            "model_name": self.model_name,
            "is_available": self.is_available(),
            "cloud_free": True,
            "local_load": "0% CPU / 0MB RAM"
        }
