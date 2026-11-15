# callerBot

![Python](https://img.shields.io/badge/python-3.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-2496ED)

Telegram-бот для групповых чатов с тремя функциями:

- **Call all** — одной командой упоминает всех участников чата.
- **Скачивание видео** — отправляет в чат ролик по ссылке из TikTok, Instagram, YouTube Shorts или RedNote.
- **Сводка чата** — `/summary` пересказывает последние сообщения группы с помощью LLM.

Построен на [aiogram](https://github.com/aiogram/aiogram) (бот) и [Kurigram](https://github.com/KurimuzonAkuma/kurigram) (форк Pyrogram, нужен для получения списка участников), видео достаёт [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Возможности

| Функция | Как использовать | Ограничение |
| --- | --- | --- |
| Позвать всех | `/all`, `/list` или `/team` в группе | 1 раз в 30 секунд на чат |
| Видео | Отправить ссылку на видео в чат | 1 запрос в 10 секунд на пользователя, не более 2 параллельных загрузок |
| Сводка | `/summary [N]` в супергруппе, N от 1 до 500 (по умолчанию 100) | 1 раз в 5 минут на чат, только супергруппы; нужен `LLM_API_KEY`. 500 сообщений читаются ~1 мин (лимиты Telegram) |

Поддерживаемые источники: TikTok (видео и слайдшоу), Instagram, YouTube Shorts (только `/shorts/`), RedNote (`xhslink.com`).

## Быстрый старт (Docker)

1. Создайте бота у [@BotFather](https://t.me/BotFather) и получите `BOT_TOKEN`.
2. Получите `API_ID` и `API_HASH` на [my.telegram.org](https://my.telegram.org).
3. Создайте `.env` в корне проекта:

   ```env
   BOT_TOKEN=123456:ABC...
   API_ID=12345
   API_HASH=0123456789abcdef
   ```

4. Запустите:

   ```bash
   docker compose build
   docker compose up -d
   ```

5. Добавьте бота в группу. Чтобы он видел ссылки и список участников, отключите Privacy Mode в BotFather (`/setprivacy` → Disable) и/или сделайте бота администратором.

Логи: `docker compose logs -f`. Остановка: `docker compose stop`.

## Конфигурация

| Переменная | Обязательна | Описание |
| --- | --- | --- |
| `BOT_TOKEN` | да | Токен бота |
| `API_ID`, `API_HASH` | да | Данные приложения Telegram (нужны всегда, в том числе для `/all`) |
| `VIDEO_DOWNLOAD_ENABLED` | нет | `false`/`0`/`no`/`off` отключает скачивание видео, остаётся только `/all`. По умолчанию `true` |
| `LLM_API_KEY` | нет | Ключ OpenAI-совместимого API для `/summary`. Пусто — команда выключена |
| `LLM_BASE_URL` | нет | База API, по умолчанию `https://openrouter.ai/api/v1` |
| `LLM_MODEL` | нет | Модель, по умолчанию `deepseek/deepseek-v4.1-flash` |
| `BLACKLIST` | нет | Telegram ID пользователей через запятую, чьи ссылки игнорируются |

Бот падает при старте, если обязательная переменная не задана.

> **Приватность:** `/summary` отправляет тексты сообщений чата (имена, @username, текст) внешнему LLM-провайдеру. Включайте только если участники согласны. Системный промпт лежит в `src/prompts/summary.md`.

Предпросмотр сводки на живом чате без запуска бота (ссылка на сообщение — граница):

```bash
uv run --no-sync --env-file .env python src/summary_preview.py https://t.me/c/<chat>/<id> [N=100] [--dry]
```

## Локальная разработка

Требуется [uv](https://docs.astral.sh/uv/) и ffmpeg в `PATH`.

```bash
uv sync --no-install-package tgcrypto   # на Windows TgCrypto не собирается без Visual Studio
cd src && uv run --no-sync python main.py
```

Без `tgcrypto` Kurigram работает медленнее, но работает. В Docker он собирается автоматически.

Линтер:

```bash
uv run --no-sync ruff check src
uv run --no-sync ruff format src
```

Обновить yt-dlp (ломается при изменениях на стороне платформ): `uv lock --upgrade-package yt-dlp`, затем `docker compose build`.

## Архитектура

```text
src/
├── main.py              # aiogram Dispatcher + единственный pyrogram Client
├── handlers/            # call_all_handler, video_handler, summary_handler
├── downloaders/         # downloader.py (реестр), ytdlp.py, tiktok/
├── apis/                # api.py (общая HTTP-сессия), llm.py (summarize)
├── prompts/summary.md   # системный промпт сводки
└── utils/               # config, urls, throttle, ...
```

- Тип ссылки определяется только по hostname в `utils/urls.get_source`.
- Новый источник: добавить хост в `SOURCE_HOSTS` и загрузчик в `DOWNLOADERS` (`downloaders/downloader.py`).
- Один `pyrogram.Client` создаётся в `main()` и передаётся в хендлеры через DI aiogram.
- ffmpeg/ffprobe запускаются асинхронно через `run_command`, чтобы не блокировать event loop.

### Не проверено

- `/summary` читает историю чата через `get_messages` по ID (`channels.getMessages`). Проверено только для бота-администратора в супергруппе. Работает ли чтение, когда бот **не** администратор и Privacy Mode включён, — не проверялось.

## Безопасность деплоя

Контейнер работает от non-root (uid 1000), с read-only корневой ФС, `cap_drop: ALL` и `no-new-privileges`. Записываемый том — `./data` (там лежит `caller.session` и временные файлы).

## Лицензия

[MIT](LICENSE)
