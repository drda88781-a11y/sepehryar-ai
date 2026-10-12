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

    # LAN and Local CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def no_cache_middleware(request, call_next):
        response = await call_next(request)
        if request.url.path.endswith((".html", "/", ".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    app.include_router(router)

    from pathlib import Path
    manual_images_dir = Path(__file__).resolve().parent.parent.parent / "knowledge_base" / "manuals" / "images"
    if manual_images_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/images", StaticFiles(directory=str(manual_images_dir)), name="manual_images")

    web_dir = Path(__file__).resolve().parent.parent.parent / "web"
    if web_dir.exists():
        from fastapi.staticfiles import StaticFiles
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")

    return app


def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> None:
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
