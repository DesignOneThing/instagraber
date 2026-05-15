# INSTAGRAB

INSTAGRAB — Telegram-бот, который принимает ссылку на Instagram-пост, Reel или карусель и отправляет:

- исходное видео целиком;
- видео без звука;
- звук отдельно;
- картинку, если пост является фото.

## Что нужно установить

1. Python 3.11+
2. `ffmpeg`
3. зависимости проекта:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

На macOS `ffmpeg` обычно ставится так:

```bash
brew install ffmpeg
```

## Настройка

1. Создай бота через [@BotFather](https://t.me/BotFather).
2. Скопируй `.env.example` в `.env`.
3. Вставь токен в `TELEGRAM_BOT_TOKEN`.

Если Instagram не отдает пост без авторизации, экспортируй cookies из браузера в Netscape-формате и укажи путь:

```env
INSTAGRAM_COOKIES_FILE=/absolute/path/to/instagram_cookies.txt
```

## Запуск

```bash
.venv/bin/python -m instagrab
```

После запуска отправь боту ссылку на Instagram-пост или Reel.

## Важные ограничения

Telegram Bot API обычно принимает файлы до 50 MB при обычной отправке ботом. Если ролик больше лимита, бот скачает и обработает его, но сообщит, что файл слишком большой для отправки.

Скачивай и обрабатывай только те материалы, на которые у тебя есть права или разрешение.
