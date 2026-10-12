"""
Production Web & API Runner for Cloud Deployment (Liara, Docker, VPS).
Runs FastAPI server with static web UI and full AI Cognitive Engine.
"""
import os
import sys

# Ensure UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.api.server import create_api_app
from app.core.lifecycle import initialize_application
import uvicorn

app = create_api_app()

if __name__ == "__main__":
    initialize_application()
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 Starting Production Sepehryar AI Server on http://{host}:{port} ...")
    uvicorn.run("start_production:app", host=host, port=port, workers=2)
