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


def verify_loopback_client(request: Request) -> None:
    """Ensure API requests strictly originate from local loopback interface."""
    client_host = request.client.host if request.client else "unknown"
    allowed_hosts = {"127.0.0.1", "::1", "localhost", "testclient"}

    if client_host not in allowed_hosts:
        logger.warning(f"Forbidden remote access attempt blocked from IP: {client_host}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="دسترسی به وب‌سرویس هوش مصنوعی سپهریار تنها از طریق آدرس لوکال (127.0.0.1) مجاز است."
        )


def verify_api_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> bool:
    """Validate Bearer token or X-API-Key header against configured settings."""
    # First verify loopback
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
