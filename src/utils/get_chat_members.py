import os

from pyrogram import Client, utils


def get_peer_type_new(peer_id: int) -> str:
    peer_id_str = str(peer_id)
    if not peer_id_str.startswith("-"):
        return "user"
    elif peer_id_str.startswith("-100"):
        return "channel"
    else:
        return "chat"


async def get_chat_members(chat_id: int) -> list[int]:
    utils.get_peer_type = get_peer_type_new

    members = []

    async with Client("caller",
                      api_id=os.getenv('API_ID'),
                      api_hash=os.getenv('API_HASH'),
                      bot_token=os.getenv('BOT_TOKEN')) as client:
        async for member in client.get_chat_members(chat_id):
            if not member.user.is_bot:
                members.append(member.user.id)

    return members
