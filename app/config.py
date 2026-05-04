import tempfile
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_THUMB_CACHE = Path(tempfile.gettempdir()) / "pageviewer" / "thumbs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # All file access is restricted to paths under ALLOWED_ROOT.
    ALLOWED_ROOT: Path = Path.home()
    # If set, GET /api/dirs with no `path` lists this folder first (must be under ALLOWED_ROOT).
    BROWSE_START_PATH: Path | None = None

    # Absolute path recommended; empty/relative values are normalized (never the app cwd).
    THUMB_CACHE_DIR: Path = _DEFAULT_THUMB_CACHE
    THUMB_SIZE: int = 150
    PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    DIR_BROWSER_PAGE_SIZE: int = 50
    MAX_DIR_BROWSER_PAGE_SIZE: int = 200
    OVERLAY_CACHE_SIZE: int = 50
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    FRONTEND_DIST: Path | None = None

    @field_validator("FRONTEND_DIST", "BROWSE_START_PATH", mode="before")
    @classmethod
    def optional_path(cls, v):
        if v is None or v == "":
            return None
        return Path(v)

    @field_validator("THUMB_CACHE_DIR", mode="before")
    @classmethod
    def thumb_cache_absolute(cls, v):
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return _DEFAULT_THUMB_CACHE
        p = Path(v).expanduser()
        if not p.is_absolute():
            # Never resolve relative paths from the process cwd (avoids writing next to uvicorn).
            return (_DEFAULT_THUMB_CACHE.parent / p).resolve()
        return p.resolve()


settings = Settings()
