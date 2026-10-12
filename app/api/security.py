"""
API Authentication and Loopback Security Guards.
"""
from typing import Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config.settings import settings
from app.core.logger import get_logger

logger = get_logger("api.security")

security_bearer = HTTPBearer(auto_error=False)


def is_trusted_network_host(client_host: str) -> bool:
    """Check if host is loopback or local private network (LAN)."""
    if client_host in {"127.0.0.1", "::1", "localhost", "testclient"}:
        return True
    try:
        import ipaddress
        ip = ipaddress.ip_address(client_host)
        return ip.is_private or ip.is_loopback
    except (ValueError, Exception):
        return False


def verify_loopback_client(request: Request) -> None:
    """Ensure API requests strictly originate from loopback or trusted private LAN."""
    client_host = request.client.host if request.client else "unknown"

    if not is_trusted_network_host(client_host):
        logger.warning(f"Forbidden remote access attempt blocked from IP: {client_host}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی به وب‌سرویس هوش مصنوعی سپهریار تنها از طریق شبکه محلی (LAN) یا لوکال مجاز است."
        )


def verify_api_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> bool:
    # If strict offline mode is explicitly enabled, enforce loopback check
    if settings.offline_strict:
        verify_loopback_client(request)

    # If debug mode or no token configured, allow
    if not settings.api_token:
        return True

    # 1. Check Bearer token
    if credentials and credentials.credentials == settings.api_token:
        return True

    # 2. Check X-API-Key header
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header == settings.api_token:
        return True

    logger.warning("Unauthorized API call with invalid or missing security token.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="توکن دسترسی معتبر نمی‌باشد. لطفاً هدر Authorization یا X-API-Key را بررسی کنید.",
        headers={"WWW-Authenticate": "Bearer"},
    )
