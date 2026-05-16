from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL

from instagrab.media_tools import ffmpeg_executable


INSTAGRAM_URL_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/[^\s<>]+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DownloadedMedia:
    path: Path
    kind: str
    title: str
    index: int


def extract_instagram_url(text: str) -> str | None:
    match = INSTAGRAM_URL_RE.search(text.strip())
    if not match:
        return None
    return match.group(0).rstrip(".,)]}")


def is_instagram_post_url(text: str) -> bool:
    return extract_instagram_url(text) is not None


def download_instagram_media(
    url: str,
    output_dir: Path,
    *,
    cookies_file: Path | None = None,
    max_download_bytes: int,
) -> list[DownloadedMedia]:
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts: dict[str, Any] = {
        "outtmpl": str(output_dir / "%(playlist_index|1)02d-%(id)s.%(ext)s"),
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "noplaylist": False,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 90,
        "retries": 5,
        "fragment_retries": 5,
        "file_access_retries": 5,
        "extractor_retries": 5,
        "max_filesize": max_download_bytes,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
            )
        },
    }

    ffmpeg_path = ffmpeg_executable()
    if ffmpeg_path is not None:
        ydl_opts["ffmpeg_location"] = ffmpeg_path

    if cookies_file is not None:
        ydl_opts["cookiefile"] = str(cookies_file)

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    entries = _flatten_entries(info)
    downloaded: list[DownloadedMedia] = []

    for index, entry in enumerate(entries, start=1):
        path = _resolve_downloaded_path(entry)
        if path is None or not path.exists():
            continue

        media_kind = "video" if _looks_like_video(entry, path) else "image"
        title = str(entry.get("title") or entry.get("description") or "Instagram media")
        downloaded.append(DownloadedMedia(path=path, kind=media_kind, title=title, index=index))

    if not downloaded:
        raise RuntimeError("Не удалось найти скачанные файлы для этой ссылки.")

    return downloaded


def _flatten_entries(info: dict[str, Any]) -> list[dict[str, Any]]:
    entries = info.get("entries")
    if not entries:
        return [info]
    return [entry for entry in entries if entry]


def _resolve_downloaded_path(entry: dict[str, Any]) -> Path | None:
    requested = entry.get("requested_downloads") or []
    for item in requested:
        filepath = item.get("filepath")
        if filepath:
            return Path(filepath)

    filepath = entry.get("filepath") or entry.get("_filename")
    return Path(filepath) if filepath else None


def _looks_like_video(entry: dict[str, Any], path: Path) -> bool:
    if entry.get("vcodec") and entry.get("vcodec") != "none":
        return True
    return path.suffix.lower() in {".mp4", ".mov", ".mkv", ".webm"}
