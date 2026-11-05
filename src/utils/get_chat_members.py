from pyrogram import Client


async def get_chat_members(client: Client, chat_id: int) -> list[int]:
    return [
        m.user.id async for m in client.get_chat_members(chat_id) if not m.user.is_bot
    ]
