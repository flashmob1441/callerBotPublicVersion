import asyncio
import logging
import random

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.types import Message
from pyrogram import Client

from utils.get_chat_members import get_chat_members
from utils.throttle import allow
from utils.variables import EMOJI_LIST

logger = logging.getLogger(__name__)

router = Router(name=__name__)

CHUNK_SIZE = 5
PAUSE_SECONDS = 0.5
ALL_COOLDOWN = 30  # seconds per chat


@router.message(
    Command("all", "list", "team"), F.chat.type.in_({"group", "supergroup"})
)
async def call_all_handler(message: Message, pyro_client: Client) -> None:
    if not allow(("all", message.chat.id), ALL_COOLDOWN):
        return
    members_id = await get_chat_members(pyro_client, message.chat.id)
    mentions = [
        f"[{random.choice(EMOJI_LIST)}](tg://user?id={member_id})"
        for member_id in members_id
    ]

    for i in range(0, len(mentions), CHUNK_SIZE):
        text = "".join(mentions[i : i + CHUNK_SIZE])
        try:
            try:
                await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await message.answer(text=text, parse_mode=ParseMode.MARKDOWN_V2)
        except TelegramAPIError:
            logger.exception("Failed to send mentions to chat %s", message.chat.id)
            return
        await asyncio.sleep(PAUSE_SECONDS)
