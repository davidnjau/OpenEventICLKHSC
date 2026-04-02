"""
Central configuration — all values are read from environment variables.
A .env file in the project root is loaded automatically by python-dotenv.
"""

from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── KHSC API ──────────────────────────────────────────────────────────── #
    khsc_api_url: str = "http://localhost:9090/api/index.php"
    khsc_api_username: str
    khsc_authorization: str          # e.g. "Bearer tok_test_..."
    khsc_pass_key: str
    khsc_secret_key: str

    # ── Open Event API ────────────────────────────────────────────────────── #
    open_event_base_url: str = "http://localhost:8080/v1"
    open_event_admin_email: str
    open_event_admin_password: str

    # ── Sync settings ─────────────────────────────────────────────────────── #
    # Event ID to sync delegates into
    khsc_event_id: int = 1

    # How often to run each scheduled job (seconds)
    import_interval_seconds: int = 300    # 5 minutes
    sync_interval_seconds: int = 120      # 2 minutes

    # ── App settings ──────────────────────────────────────────────────────── #
    log_level: str = "INFO"
    middleware_port: int = 7000
    enable_scheduler: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
