from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "D&D Compendium"
    database_url: str = "sqlite:////data/compendium.sqlite3"
    asset_root: Path = Path("/data/assets")

    # Open5e v2 exposes a discoverable root. Leave OPEN5E_ENDPOINTS empty to
    # import every content endpoint returned by that root.
    open5e_api_root: str = "https://api.open5e.com/v2/"
    open5e_endpoints: str = ""
    # Conservative defaults intentionally favor API and SQLite stability over raw speed.
    open5e_page_size: int = 50
    open5e_timeout: float = 60.0
    open5e_commit_every: int = 50
    open5e_request_delay: float = 0.75
    open5e_endpoint_delay: float = 2.0
    open5e_retry_attempts: int = 5
    open5e_retry_base_delay: float = 2.0
    open5e_retry_max_delay: float = 60.0
    open5e_user_agent: str = "dnd-compendium/0.21.0"

    secret_key: str = "change-me"
    default_admin_username: str = "admin"
    default_admin_password: str = "change-me-now"
    session_cookie_name: str = "dnd_compendium_session"
    session_max_age: int = 1209600
    session_https_only: bool = False
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def endpoint_names(self) -> list[str]:
        return [x.strip() for x in self.open5e_endpoints.split(",") if x.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
