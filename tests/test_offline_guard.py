"""
Tests for OfflineGuard network enforcement.
"""
import socket
import pytest
from app.core.exceptions import OfflineViolationError
from app.core.offline_guard import (
    is_local_or_private_host,
    enforce_offline_mode,
    disable_offline_mode,
)


def test_private_and_loopback_hosts_allowed():
    """Verify loopback and LAN IPs are permitted."""
    assert is_local_or_private_host("127.0.0.1") is True
    assert is_local_or_private_host("localhost") is True
    assert is_local_or_private_host("::1") is True
    assert is_local_or_private_host("192.168.1.100") is True
    assert is_local_or_private_host("10.0.0.15") is True
    assert is_local_or_private_host("172.16.5.20") is True


def test_public_internet_hosts_blocked():
    """Verify external public internet IPs are identified as non-local."""
    assert is_local_or_private_host("8.8.8.8") is False
    assert is_local_or_private_host("1.1.1.1") is False


def test_socket_connect_raises_when_offline_enforced():
    """Verify socket connection to public IP raises OfflineViolationError."""
    try:
        enforce_offline_mode()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with pytest.raises(OfflineViolationError):
            s.connect(("8.8.8.8", 53))
        s.close()
    finally:
        disable_offline_mode()
