"""Application settings read from environment variables."""

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

REQUIRED = ("TEAM_USERNAME", "TEAM_PASSWORD", "SESSION_SECRET")


@dataclass(frozen=True)
class Settings:
    """All runtime configuration in one place."""

    team_username: str
    team_password: str
    session_secret: str
    gemini_api_key: str | None
    database_url: str


@lru_cache
def get_settings() -> Settings:
    """Load settings once from the environment (and .env if present)."""
    load_dotenv()
    missing = [name for name in REQUIRED if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}. "
                           "Copy .env.example to .env and fill them in.")
    return Settings(
        team_username=os.environ["TEAM_USERNAME"],
        team_password=os.environ["TEAM_PASSWORD"],
        session_secret=os.environ["SESSION_SECRET"],
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        database_url=os.getenv("DATABASE_URL", "sqlite:///./support.db"),
    )
