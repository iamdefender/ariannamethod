"""
Termux-specific config - no Telegram validation
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

# Load variables from .bashrc / environment
load_dotenv()


@dataclass
class Settings:
    """Termux config - no Telegram required"""

    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.85"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    db_path: str = os.getenv("ST_DB", "supertime.db")
    hero_ctx_cache_dir: Path = Path(os.getenv("HERO_CTX_CACHE_DIR", ".hero_ctx_cache"))

    def validate(self) -> None:
        """Ensure API key is present"""
        if not self.openai_api_key:
            raise RuntimeError("Missing OPENAI_API_KEY environment variable")


settings = Settings()

