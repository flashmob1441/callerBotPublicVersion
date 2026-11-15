import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pyrogram import Client

from apis.api import close_session
from handlers import admin_handler, call_all_handler, summary_handler, video_handler
from utils import storage
from utils.config import (
    ADMIN_IDS,
    API_HASH,
    API_ID,
    BOT_TOKEN,
    LLM_API_KEY,
    VIDEO_DOWNLOAD_ENABLED,
)

logger = logging.getLogger(__name__)


async def main() -> None:
    storage.init()
    dp = Dispatcher()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Админка первой: её FSM-хендлеры должны перехватить сообщения админа раньше остальных.
    if ADMIN_IDS:
        dp.include_router(admin_handler.router)
    else:
        logger.info("Admin panel is disabled (ADMIN_IDS is not set)")
    dp.include_router(call_all_handler.router)
    if VIDEO_DOWNLOAD_ENABLED:
        dp.include_router(video_handler.router)
    else:
        logger.info("Video download is disabled (VIDEO_DOWNLOAD_ENABLED=false)")
    if LLM_API_KEY:
        dp.include_router(summary_handler.router)
    else:
        logger.info("Summary is disabled (LLM_API_KEY is not set)")

    pyro_client = Client(
        "caller",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workdir=".",
    )
    await pyro_client.start()
    try:
        await dp.start_polling(bot, pyro_client=pyro_client)
    finally:
        await pyro_client.stop()
        await close_session()


if __name__ == "__main__":
    console_out = logging.StreamHandler()
    logging.basicConfig(
        handlers=(console_out,),
        format="[%(asctime)s | %(levelname)s]: %(message)s",
        datefmt="%m.%d.%Y %H:%M:%S",
        level=logging.INFO,
    )
    asyncio.run(main())
