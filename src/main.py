import os
import time
import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from handlers import call_all_handler, video_handler


async def main() -> None:
    dp = Dispatcher()
    bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_routers(call_all_handler.router, video_handler.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    start_timestamp = time.strftime("%Y%m%d-%H%M%S")
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(console_out, ),
                        format='[%(asctime)s | %(levelname)s]: %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.INFO)
    asyncio.run(main())
