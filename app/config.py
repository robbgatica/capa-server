"""Configuration management for capa-server."""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Paths
    capa_rules_path: Path = Path("/app/rules")
    database_path: Path = Path("/app/data/capa.db")
    upload_dir: Path = Path("/app/data/uploads")
    results_dir: Path = Path("/app/data/results")

    # Upload limits
    max_file_size_mb: int = 100

    # Application
    app_name: str = "capa-server"
    app_version: str = "0.1.0"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Ensure directories exist (handle permission errors in containers)
try:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.results_dir.mkdir(parents=True, exist_ok=True)
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
except PermissionError:
    # In rootless containers, directories may already exist from volume mounts
    pass
