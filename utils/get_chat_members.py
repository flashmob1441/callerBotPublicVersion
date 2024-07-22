import os

from pyrogram import Client


async def get_chat_members(chat_id: int) -> list[int]:
    members = []

    async with Client("caller",
                      api_id=os.getenv('API_ID'),
                      api_hash=os.getenv('API_HASH'),
                      bot_token=os.getenv('BOT_TOKEN')) as client:
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user.id)

    return members
