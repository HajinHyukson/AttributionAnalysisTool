import os
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError

_DOTENV_LOADED = False


def _default_cache_dir() -> Path:
    configured = (os.getenv("AAT_CACHE_DIR") or "").strip()
    if configured:
        return Path(configured)
    return Path(".cache")


@dataclass(frozen=True)
class Settings:
    fmp_api_key: str
    fmp_base_url: str = "https://financialmodelingprep.com/stable"
    request_timeout_seconds: int = 30
    default_years: int = 3
    cache_dir: Path = _default_cache_dir()
    cache_ttl_hours: int = 24
    default_covariance_method: str = "ledoit_wolf"
    default_ewma_decay: float = 0.94


def _load_dotenv_if_available() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return

    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        _DOTENV_LOADED = True
        return

    load_dotenv()
    _DOTENV_LOADED = True


def get_settings() -> Settings:
    _load_dotenv_if_available()
    api_key = (os.getenv("FMP_API_KEY") or "").strip()
    if not api_key:
        raise ConfigError(
            "Missing FMP_API_KEY. Set it in your environment or add "
            "`FMP_API_KEY=your_key_here` to a `.env` file."
        )
    return Settings(fmp_api_key=api_key)
