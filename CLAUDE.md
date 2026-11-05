# callerBot

Telegram-бот (aiogram + Pyrogram): "call all" и скачивание видео (TikTok, Instagram, YouTube Shorts, RedNote).

## Commands
- Установка зависимостей локально (Windows): `uv sync --no-install-package tgcrypto`
- Обновить все либы: `uv lock --upgrade && uv sync --no-install-package tgcrypto`
- Добавить зависимость: `uv add <pkg>`
- Проверка импортов: `cd src && BOT_TOKEN=1:x uv run --no-sync python -c "import main"`
- Запуск локально: `cd src && uv run --no-sync python main.py` (нужен `.env`: BOT_TOKEN, API_ID, API_HASH)
- Docker: `docker compose build` / `docker compose up -d` / `docker compose logs -f` (или `make build|run|logs`)

## Conventions
- Зависимости только в `pyproject.toml` без upper-pin, версии фиксирует `uv.lock`. `requirements.txt` не используется.
- Python 3.13 (`.python-version`).
- Исходники в `src/`, импорты от корня `src/` (запуск из `src`).

## Gotchas
- `TgCrypto` не собирается на Windows без Visual Studio — локально ставим с `--no-install-package tgcrypto` (Pyrogram работает медленнее, но работает). В Docker собирается в builder-стадии.
- Docker: образ multi-stage, non-root (uid 1000), корневая ФС read-only. CWD контейнера `/data` (том `./data`): там `caller.session` и временные файлы TikTok-слайдшоу.
- Имя образа в Docker должно быть в нижнем регистре (`caller_bot`).
- Если `.venv` ссылается на несуществующий Python — `rm -rf .venv && uv sync --no-install-package tgcrypto`.
