import logging
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.chat_type import ChatTypeFilter
from utils.get_chat_members import get_chat_members
from utils.variables import EMOJI_LIST

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.message(ChatTypeFilter(chat_type=['group', 'supergroup']), Command('all'))
async def command_call_all_handler(message: Message) -> None:
    chat_id = message.chat.id
    members_id = await get_chat_members(chat_id)
    mentions = [f'[{random.choice(EMOJI_LIST)}](tg://user?id={member_id})' for member_id in members_id]
    chunks = [mentions[x:x+5] for x in range(0, len(mentions), 5)]

    for chunk in chunks:
        answer = ''.join(chunk)
        await message.answer(
            text=answer,
            allow_sending_without_reply=True
        )
