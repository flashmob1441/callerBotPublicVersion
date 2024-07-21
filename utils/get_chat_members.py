from pyrogram import Client

from config import BOT_TOKEN, API_ID, API_HASH


async def get_chat_members(chat_id: int) -> list[int]:
    members = []

    async with Client("caller",
                      api_id=API_ID,
                      api_hash=API_HASH,
                      bot_token=BOT_TOKEN) as client:
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user.id)

    return members
