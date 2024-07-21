import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import call_all, videos

logger = logging.getLogger(__name__)


async def main() -> None:
    dp = Dispatcher()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
    dp.include_routers(call_all.router, videos.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    file_log = logging.FileHandler('log.log', mode='w', encoding='utf-8')
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(file_log, console_out),
                        format='[%(asctime)s | %(levelname)s]: %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.DEBUG)
    asyncio.run(main())
