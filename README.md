# INSTAGRAB

INSTAGRAB — Telegram-бот, который принимает ссылку на Instagram-пост, Reel или карусель и отправляет:

- исходное видео целиком;
- видео без звука;
- звук отдельно;
- картинку, если пост является фото.

## Локальный запуск

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Создай бота через [@BotFather](https://t.me/BotFather), вставь токен в `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:replace_me
```

Запуск:

```bash
.venv/bin/python -m instagrab
```

После запуска отправь боту ссылку на Instagram-пост или Reel.

## Деплой на Render

Проект уже готов для Render:

- `render.yaml` — blueprint для Render;
- `Procfile` — web-команда запуска;
- `runtime.txt` — версия Python;
- `/health` — health-check endpoint для Render;
- `imageio-ffmpeg` — bundled `ffmpeg`, чтобы не зависеть от системной установки.

Шаги:

1. Закинь проект в GitHub.
2. На Render выбери `New` -> `Blueprint` и подключи репозиторий.
3. Render прочитает `render.yaml` и создаст web service `instagrab`.
4. В Environment добавь `TELEGRAM_BOT_TOKEN` со значением токена от BotFather.
5. Нажми Deploy.

Бот работает через Telegram polling, webhook настраивать не нужно. Render требует открытый HTTP-порт для web service, поэтому INSTAGRAB автоматически поднимает `/health`, когда Render задает переменную `PORT`.

## Instagram cookies

Instagram иногда не отдает посты без авторизации. Локально можно использовать файл cookies:

```env
INSTAGRAM_COOKIES_FILE=/absolute/path/to/instagram_cookies.txt
```

На Render удобнее добавить secret environment variable:

```env
INSTAGRAM_COOKIES_TEXT=# Netscape HTTP Cookie File
```

В `INSTAGRAM_COOKIES_TEXT` нужно вставить содержимое cookies в Netscape-формате.

## Лимиты

Telegram Bot API обычно принимает файлы до 50 MB при обычной отправке ботом. Если ролик больше лимита, бот скачает и обработает его, но сообщит, что файл слишком большой для отправки.

Скачивай и обрабатывай только те материалы, на которые у тебя есть права или разрешение.
