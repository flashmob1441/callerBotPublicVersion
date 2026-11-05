import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pyrogram import Client

from apis.api import close_session
from handlers import call_all_handler, video_handler
from utils.config import API_HASH, API_ID, BOT_TOKEN


async def main() -> None:
    dp = Dispatcher()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_routers(call_all_handler.router, video_handler.router)

    pyro_client = Client(
        "caller", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
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
