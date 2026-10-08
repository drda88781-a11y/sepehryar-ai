"""
Local REST API package for Sepehryar AI Engine.
Provides secure loopback REST endpoints for external Sepehryar services and tools.
"""
from app.api.server import create_api_app

__all__ = ["create_api_app"]
