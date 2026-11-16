import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import LinkPreviewOptions, Message
from pyrogram import Client

from apis.llm import render_summary, summarize
from utils import storage
from utils.chat_history import fetch_lines
from utils.config import BLACKLIST
from utils.throttle import allow, reset

logger = logging.getLogger(__name__)

router = Router(name=__name__)

DEFAULT_N = 100
MAX_N = 500
SUMMARY_COOLDOWN = 300  # seconds per chat
FETCH_TIMEOUT = 150  # 500 messages: ~2 FLOOD_WAITs of ~30 s
HINT_COOLDOWN = 30  # seconds per chat between bot hints


def parse_n(arg: str) -> int | None:
    # [0-9], а не isdecimal(): иначе проходят Unicode-цифры и гигантские строки
    if not arg:
        return DEFAULT_N
    if not re.fullmatch(r"[0-9]{1,3}", arg):
        return None
    n = int(arg)
    return n if 1 <= n <= MAX_N else None


async def _hint(message: Message, text: str) -> None:
    # Без лимита каждая кривая команда = сообщение бота (спам, лимит Telegram на группу)
    if allow(("summary_hint", message.chat.id), HINT_COOLDOWN):
        await message.reply(text)


@router.message(Command("summary"), F.chat.type == "group")
async def summary_group_handler(message: Message) -> None:
    await message.reply("Сводка работает только в супергруппах")


@router.message(Command("summary"), F.chat.type == "supergroup")
async def summary_handler(
    message: Message, command: CommandObject, pyro_client: Client
) -> None:
    chat_id = message.chat.id
    if message.from_user and message.from_user.id in BLACKLIST:
        return
    n = parse_n((command.args or "").strip())
    if n is None:
        await _hint(message, f"Использование: /summary [1-{MAX_N}]")
        return
    if not storage.is_chat_allowed(chat_id):
        logger.info("Summary not enabled in chat %s (%s)", chat_id, message.chat.title)
        await _hint(message, "Сводка не включена в этом чате")
        return
    key = ("summary", chat_id)
    if not allow(key, SUMMARY_COOLDOWN):
        await message.reply("Сводку можно запрашивать раз в 5 минут")
        return

    status = await message.reply(
        f"Читаю {n} сообщений…" + (" Это займёт ~1 мин" if n > 200 else "")
    )
    thread_id = message.message_thread_id if message.is_topic_message else None
    try:
        async with asyncio.timeout(FETCH_TIMEOUT):
            lines = await fetch_lines(
                pyro_client,
                chat_id,
                message.message_id,
                n,
                thread_id,
                names=storage.get_names(),
            )
        if not lines:
            reset(key)
            await status.edit_text("Нет сообщений для сводки")
            return
        await status.edit_text("Анализирую…")
        text = await summarize(lines)
        await status.edit_text(
            **render_summary(text).as_kwargs(),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except TimeoutError:
        reset(key)
        logger.warning("Summary fetch timed out in chat %s", chat_id)
        await status.edit_text("Telegram ограничил запросы, попробуйте позже")
    except Exception:
        reset(key)
        logger.exception("Summary failed in chat %s", chat_id)
        await status.edit_text("Не удалось сделать сводку, попробуйте позже")
