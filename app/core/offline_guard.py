"""
Strict offline enforcement guard.
Prevents any outbound HTTP/TCP connections to the public internet while allowing
local loopback (127.0.0.1) and LAN connections for on-premise SQL Server.
"""
import ipaddress
import socket
from typing import Optional
from app.core.exceptions import OfflineViolationError
from app.core.logger import get_logger

logger = get_logger("offline_guard")

# Keep original references for restoration/testing
_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection
_GUARD_ACTIVE = False


def is_local_or_private_host(host: str) -> bool:
    """
    Check if a given host/IP is strictly local or within an on-premise private subnet.
    Allowed:
      - localhost, 127.0.0.1, ::1
      - Windows Named Pipes
      - RFC1918 Private Subnets (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
      - Link-local (169.254.0.0/16)
    Denied:
      - Any public internet IP or external domain
    """
    if not host:
        return True

    # Named pipes and local indicators
    if host.startswith(r"\\") or host in (".", "localhost", "127.0.0.1", "::1"):
        return True

    # Strip port if present
    clean_host = host.split(":")[0].strip()

    try:
        ip = ipaddress.ip_address(clean_host)
        return ip.is_loopback or ip.is_private or ip.is_link_local
    except ValueError:
        # It is a hostname. Check if it resolves to a private or loopback IP.
        try:
            resolved_ip_str = socket.gethostbyname(clean_host)
            resolved_ip = ipaddress.ip_address(resolved_ip_str)
            return resolved_ip.is_loopback or resolved_ip.is_private or resolved_ip.is_link_local
        except Exception:
            # Cannot resolve or external domain
            return False


def enforce_offline_mode() -> None:
    """
    Monkey-patch socket connections to guarantee zero external data leakage.
    Any attempt to connect to external internet will raise OfflineViolationError.
    """
    global _GUARD_ACTIVE
    if _GUARD_ACTIVE:
        return

    def guarded_connect(self, address):
        if isinstance(address, tuple) and len(address) >= 1:
            host = address[0]
            if not is_local_or_private_host(str(host)):
                msg = f"Outbound connection to public internet host blocked by OfflineGuard: {host}"
                logger.error(msg)
                raise OfflineViolationError(
                    user_message="ارتباط با اینترنت مسدود است. سامانه سپهریار در حالت ۱۰۰٪ آفلاین فعالیت می‌کند.",
                    technical_details=msg
                )
        return _ORIGINAL_CONNECT(self, address)

    socket.socket.connect = guarded_connect
    _GUARD_ACTIVE = True
    logger.info("OfflineGuard is ACTIVE. All external internet egress is strictly blocked.")


def disable_offline_mode() -> None:
    """Disable offline guard (useful for unit tests)."""
    global _GUARD_ACTIVE
    if not _GUARD_ACTIVE:
        return
    socket.socket.connect = _ORIGINAL_CONNECT
    _GUARD_ACTIVE = False
    logger.warning("OfflineGuard has been DISABLED.")
