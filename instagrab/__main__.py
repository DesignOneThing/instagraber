from __future__ import annotations

import asyncio
import logging
import os
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from instagrab.config import Settings, load_settings
from instagrab.downloader import (
    DownloadedMedia,
    download_instagram_media,
    is_instagram_post_url,
)
from instagrab.media_tools import ensure_ffmpeg_available, split_video


logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path not in {"/", "/health"}:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"INSTAGRAB is running\n")

    def log_message(self, format: str, *args: object) -> None:
        logger.debug("Health server: " + format, *args)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    del context
    if update.message is None:
        return

    await update.message.reply_text(
        "INSTAGRAB на связи. Пришли ссылку на Instagram-пост или Reel. "
        "Я отправлю исходное медиа, а для видео еще отдельно звук и видео без звука."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    url = update.message.text.strip()

    if not is_instagram_post_url(url):
        await update.message.reply_text("Нужна ссылка вида https://www.instagram.com/p/... или /reel/...")
        return

    await update.message.chat.send_action(ChatAction.TYPING)
    status_message = await update.message.reply_text("Скачиваю медиа из Instagram...")

    try:
        with tempfile.TemporaryDirectory(prefix="instagram-splitter-") as tmp:
            work_dir = Path(tmp)
            media_items = await asyncio.to_thread(
                download_instagram_media,
                url,
                work_dir / "downloads",
                cookies_file=settings.instagram_cookies_file,
                max_download_bytes=settings.max_download_bytes,
            )

            await status_message.edit_text(f"Нашел файлов: {len(media_items)}. Обрабатываю...")

            for item in media_items:
                await _send_media_item(update, item, work_dir / "processed", settings)

            await status_message.edit_text("Готово.")
    except Exception as exc:
        logger.exception("Failed to process Instagram URL")
        await status_message.edit_text(_human_error(exc))


async def _send_media_item(
    update: Update,
    item: DownloadedMedia,
    output_dir: Path,
    settings: Settings,
) -> None:
    if update.message is None:
        return

    prefix = f"#{item.index}: " if item.index > 1 else ""

    if item.kind == "image":
        await _send_file(update, item.path, f"{prefix}картинка", settings)
        return

    await _send_file(update, item.path, f"{prefix}исходное видео со звуком", settings)

    split = await split_video(item.path, output_dir)
    if split.silent_video is not None:
        await _send_file(update, split.silent_video, f"{prefix}видео без звука", settings)

    if split.audio is not None:
        await _send_file(update, split.audio, f"{prefix}звук отдельно", settings)
    else:
        await update.message.reply_text(f"{prefix}в этом видео не нашел отдельную аудиодорожку.")


async def _send_file(update: Update, path: Path, caption: str, settings: Settings) -> None:
    if update.message is None:
        return

    size = path.stat().st_size
    if size > settings.max_upload_bytes:
        size_mb = size / 1024 / 1024
        await update.message.reply_text(
            f"{caption}: файл получился {size_mb:.1f} MB, это больше лимита отправки."
        )
        return

    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
    with path.open("rb") as file:
        await update.message.reply_document(document=file, filename=path.name, caption=caption)


def _human_error(exc: Exception) -> str:
    text = str(exc)
    if "ffmpeg is not installed" in text:
        return "Не найден ffmpeg. Установи его и запусти бота снова."
    if "cookies" in text.lower() or "login" in text.lower() or "sign in" in text.lower():
        return (
            "Instagram попросил авторизацию. Добавь cookies в Netscape-формате "
            "и укажи INSTAGRAM_COOKIES_FILE в .env."
        )
    if "File is larger than max-filesize" in text:
        return "Пост слишком большой для текущего лимита MAX_DOWNLOAD_MB."
    return f"Не получилось обработать ссылку: {text[:900]}"


def main() -> None:
    settings = load_settings()
    ensure_ffmpeg_available()
    _start_health_server_if_needed()

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling(allowed_updates=Update.ALL_TYPES)



def _start_health_server_if_needed() -> None:
    port_value = os.getenv("PORT", "").strip()
    if not port_value:
        return

    server = ThreadingHTTPServer(("0.0.0.0", int(port_value)), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Health server is listening on port %s", port_value)


if __name__ == "__main__":
    main()
