"""Предпросмотр /summary на живом чате.

Запуск: cd src && uv run --no-sync --env-file ../.env python summary_preview.py \
    https://t.me/c/<chat>/<id> [N=100] [--dry]
Ссылка на сообщение — граница: берутся N сообщений строго до него и оно само.
"""

import asyncio
import re
import sys
import time

from pyrogram import Client

from apis.api import close_session
from apis.llm import summarize
from utils import storage
from utils.chat_history import fetch_lines
from utils.config import API_HASH, API_ID, BOT_TOKEN, LLM_API_KEY


async def main(link: str, limit: int, dry: bool) -> None:
    m = re.fullmatch(r"https://t\.me/c/(\d+)/(?:\d+/)?(\d+)", link)
    if not m:
        sys.exit("Ссылка должна быть вида https://t.me/c/<chat>/<id>")
    if not dry and not LLM_API_KEY:
        sys.exit("LLM_API_KEY не задан (используйте --dry)")
    chat_id, msg_id = int(f"-100{m[1]}"), int(m[2])
    storage.init()

    async with Client(
        "preview",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        in_memory=True,
        no_updates=True,
    ) as client:
        t = time.monotonic()
        lines = await fetch_lines(
            client, chat_id, msg_id + 1, limit, names=storage.get_names()
        )
    print(f"Собрано {len(lines)} строк за {time.monotonic() - t:.1f} с")
    print("\n".join(lines[:5]), "\n...", *lines[-5:], sep="\n")
    print(f"Размер лога: {sum(map(len, lines))} символов")
    if dry:
        return
    t = time.monotonic()
    try:
        text = await summarize(lines)
    finally:
        await close_session()
    print(f"\nLLM: {time.monotonic() - t:.1f} с, {len(text)} символов\n\n{text}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--dry"]
    if not args:
        sys.exit(__doc__)
    asyncio.run(
        main(args[0], int(args[1]) if len(args) > 1 else 100, "--dry" in sys.argv)
    )
