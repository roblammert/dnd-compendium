from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "D&D Compendium"
    database_url: str = "sqlite:////data/compendium.sqlite3"
    asset_root: Path = Path("/data/assets")
    open5e_base_url: str = "https://api.open5e.com"
    open5e_endpoints: str = "monsters,spells,magicitems,weapons,armor,classes,races,backgrounds,feats"
    open5e_page_size: int = 100
    secret_key: str = "change-me"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def endpoint_names(self) -> list[str]:
        return [x.strip() for x in self.open5e_endpoints.split(",") if x.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
