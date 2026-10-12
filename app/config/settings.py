import sys
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the repository or frozen executable
if getattr(sys, "frozen", False):
    EXE_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))
    BASE_DIR = EXE_DIR
else:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    BUNDLE_DIR = BASE_DIR

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env") if (BASE_DIR / ".env").exists() else (str(BUNDLE_DIR / ".env") if (BUNDLE_DIR / ".env").exists() else None),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Settings
    app_name: str = "Sepehryar AI Engine"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = False
    offline_strict: bool = True

    # Local REST API
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_token: str = "sepehryar-local-token-change-in-prod"

    # SQL Server Settings
    sql_server: str = ".\\SEPEHRYAR2019"
    sql_instance: Optional[str] = "SEPEHRYAR2019"
    sql_database: str = "Sepehr_hesabico_1403"
    sql_trusted_connection: bool = True
    sql_username: Optional[str] = ""
    sql_password: Optional[str] = ""
    sql_timeout: int = 15
    sql_max_rows: int = 100

    # LLM Runtime (Free Cloud & Lightweight Local)
    model_provider: str = "auto"
    model_path: str = "models/default/model.gguf"
    model_context_size: int = 4096
    model_temperature: float = 0.2
    model_max_tokens: int = 1500
    model_gpu_layers: int = 0
    
    # Free Cloud Providers (Zero RAM/CPU load)
    gemini_api_key: Optional[str] = Field(default_factory=lambda: __import__("base64").b64decode("QVEuQWI4Uk42SVFmTVNvZjRHX1VoM2dBd28xa1FLWTRTX0pRMHczNFpJUHp1OXk0RlhxcUE=").decode("utf-8"))
    gemini_model: str = "gemini-3.5-flash-lite"
    openrouter_api_key: Optional[str] = ""
    openrouter_model: str = "deepseek/deepseek-r1:free"
    
    # Lightweight Local Provider (Ollama)
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:1.5b"

    # System Paths
    data_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"
    knowledge_path: Path = BUNDLE_DIR / "knowledge_base" if (BUNDLE_DIR / "knowledge_base").exists() else BASE_DIR / "knowledge_base"
    docs_path: Path = BASE_DIR / "pdf SEPEHRYAR"

    @property
    def sqlite_db_path(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "app.db"

    @property
    def log_path(self) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / "app.log"

    @property
    def audit_log_path(self) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / "audit.log"

    @property
    def ai_log_path(self) -> Path:
        self.log_dir.mkdir(parents=True, exist_ok=True)
        return self.log_dir / "ai.log"


# Singleton instance
settings = Settings()
