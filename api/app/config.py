"""Application settings, loaded from api/.env."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_PATH, extra="ignore")

    database_url: str = ""
    iucn_api_token: str = ""
    inaturalist_token: str = ""
    gbif_user: str = ""
    gbif_pwd: str = ""
    gbif_email: str = ""

    @property
    def sqlalchemy_url(self) -> str:
        """Normalize a raw Postgres URI to the psycopg (v3) driver SQLAlchemy expects.

        Supabase hands you `postgresql://...`; SQLAlchemy 2 + psycopg3 wants
        `postgresql+psycopg://...`. We rewrite it so the user can paste as-is.
        """
        url = self.database_url.strip()
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        elif url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        return url


settings = Settings()
