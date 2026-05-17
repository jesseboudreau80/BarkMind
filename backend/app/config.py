from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    app_name: str = "barkmind"
    app_version: str = "1.0.0"
    environment: str = "local"
    owner: str = "jesse"
    doctrine_version: str = "2026-05-10"

    backend_port: int = 8108
    frontend_port: int = 3008

    database_url: str = "postgresql+asyncpg://barkmind_user:barkmind_dev_password@127.0.0.1:5432/barkmind"

    jwt_secret: str = "changeme"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    media_backend: str = "local"
    media_root: str = "./media"

    openclaw_base_url: str = "http://127.0.0.1:18789"
    openclaw_model: str = "claude-sonnet-4-6"

    aegis_base_url: str = "http://127.0.0.1:8102"
    aegis_user_email: str = "admin@dpvet.com"

    # Phase 6: service-to-service auth key for Aegis polling
    service_api_key: str = "barkmind-service-key-change-in-production"

    log_level: str = "INFO"


settings = Settings()
