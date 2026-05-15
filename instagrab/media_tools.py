from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

import imageio_ffmpeg


@dataclass(frozen=True)
class SplitResult:
    silent_video: Path | None
    audio: Path | None


def ensure_ffmpeg_available() -> None:
    if _ffmpeg_executable() is None:
        raise RuntimeError("ffmpeg is not installed or not available in PATH.")


async def split_video(video_path: Path, output_dir: Path) -> SplitResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    silent_video = output_dir / f"{video_path.stem}_no_audio.mp4"
    audio = output_dir / f"{video_path.stem}_audio.m4a"

    await _run_ffmpeg(
        "-y",
        "-i",
        str(video_path),
        "-map",
        "0:v:0",
        "-c",
        "copy",
        "-an",
        str(silent_video),
    )

    audio_created = True
    try:
        await _run_ffmpeg(
            "-y",
            "-i",
            str(video_path),
            "-map",
            "0:a:0",
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(audio),
        )
    except RuntimeError:
        audio_created = False

    return SplitResult(
        silent_video=silent_video if silent_video.exists() else None,
        audio=audio if audio_created and audio.exists() else None,
    )


async def _run_ffmpeg(*args: str) -> None:
    process = await asyncio.create_subprocess_exec(
        _ffmpeg_executable() or "ffmpeg",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()

    if process.returncode != 0:
        message = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(message or "ffmpeg failed")


def _ffmpeg_executable() -> str | None:
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
