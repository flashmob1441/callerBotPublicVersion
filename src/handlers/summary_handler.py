import asyncio
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from pyrogram import Client

from apis.llm import summarize
from utils.chat_history import fetch_lines
from utils.throttle import allow

logger = logging.getLogger(__name__)

router = Router(name=__name__)

DEFAULT_N = 100
MAX_N = 500
SUMMARY_COOLDOWN = 300  # seconds per chat
FETCH_TIMEOUT = 150  # 500 messages: ~2 FLOOD_WAITs of ~30 s


@router.message(Command("summary"), F.chat.type == "group")
async def summary_group_handler(message: Message) -> None:
    await message.reply("Сводка работает только в супергруппах")


@router.message(Command("summary"), F.chat.type == "supergroup")
async def summary_handler(
    message: Message, command: CommandObject, pyro_client: Client
) -> None:
    arg = (command.args or "").strip()
    n = int(arg) if arg.isdecimal() else DEFAULT_N if not arg else 0
    if not 1 <= n <= MAX_N:
        await message.reply(f"Использование: /summary [1-{MAX_N}]")
        return
    if not allow(("summary", message.chat.id), SUMMARY_COOLDOWN):
        await message.reply("Сводку можно запрашивать раз в 5 минут")
        return

    status = await message.reply(
        f"Читаю {n} сообщений…" + (" Это займёт ~1 мин" if n > 200 else "")
    )
    thread_id = message.message_thread_id if message.is_topic_message else None
    try:
        async with asyncio.timeout(FETCH_TIMEOUT):
            lines = await fetch_lines(
                pyro_client, message.chat.id, message.message_id, n, thread_id
            )
        if not lines:
            await status.edit_text("Нет сообщений для сводки")
            return
        await status.edit_text("Анализирую…")
        text = await summarize(lines)
        await status.edit_text(text[:4096], parse_mode=None)
    except TimeoutError:
        logger.warning("Summary fetch timed out in chat %s", message.chat.id)
        await status.edit_text("Telegram ограничил запросы, попробуйте позже")
    except Exception:
        logger.exception("Summary failed in chat %s", message.chat.id)
        await status.edit_text("Не удалось сделать сводку, попробуйте позже")
