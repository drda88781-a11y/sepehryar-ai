"""
Configuration and settings management using Pydantic Settings.
"""
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
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
    api_host: str = "127.0.0.1"
    api_port: int = 8765
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

    # Local LLM Runtime (Reserved for Phase 4)
    model_provider: str = "llama_cpp"
    model_path: str = "models/default/model.gguf"
    model_context_size: int = 4096
    model_temperature: float = 0.2
    model_max_tokens: int = 1024
    model_gpu_layers: int = 0

    # System Paths
    data_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"
    knowledge_path: Path = BASE_DIR / "knowledge_base"

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
