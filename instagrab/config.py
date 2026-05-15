from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    instagram_cookies_file: Path | None
    max_upload_mb: int
    max_download_mb: int

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_download_bytes(self) -> int:
        return self.max_download_mb * 1024 * 1024


def load_settings() -> Settings:
    load_dotenv()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required. Put it into .env.")

    cookies_file = _resolve_cookies_file()

    return Settings(
        telegram_bot_token=token,
        instagram_cookies_file=cookies_file,
        max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "49")),
        max_download_mb=int(os.getenv("MAX_DOWNLOAD_MB", "250")),
    )


def _resolve_cookies_file() -> Path | None:
    cookies_value = os.getenv("INSTAGRAM_COOKIES_FILE", "").strip()
    if cookies_value:
        return Path(cookies_value).expanduser()

    cookies_text = os.getenv("INSTAGRAM_COOKIES_TEXT", "").strip()
    if not cookies_text:
        return None

    cookies_file = Path(tempfile.gettempdir()) / "instagrab_instagram_cookies.txt"
    cookies_file.write_text(cookies_text + "\n", encoding="utf-8")
    return cookies_file
