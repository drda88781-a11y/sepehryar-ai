"""
FastAPI Server application factory and uvicorn runner.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.config.constants import APP_TITLE, APP_TITLE_FA, APP_VERSION
from app.config.settings import settings
from app.core.lifecycle import initialize_application
from app.core.logger import get_logger

logger = get_logger("api.server")


def create_api_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=f"{APP_TITLE} ({APP_TITLE_FA})",
        description="وب‌سرویس محلی و امن هوش مصنوعی و واکشی داده‌های مالی نرم‌افزار حسابداری سپهریار (100% آفلاین)",
        version=APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Local-only CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


def start_api_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run uvicorn server on specified loopback interface."""
    initialize_application()
    logger.info(f"Starting Sepehryar Local REST API on http://{host}:{port}...")
    app = create_api_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=False
    )
