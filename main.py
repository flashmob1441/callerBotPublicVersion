import asyncio
import logging
import os
import time

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from handlers import call_all, videos

logger = logging.getLogger(__name__)

LOG_DIR = 'logs'


async def main() -> None:
    load_dotenv()
    dp = Dispatcher()
    bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2))
    dp.include_routers(call_all.router, videos.router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    start_timestamp = time.strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(LOG_DIR, f'log-{start_timestamp}.log')
    file_logger = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    console_out = logging.StreamHandler()
    logging.basicConfig(handlers=(file_logger, console_out),
                        format='[%(asctime)s | %(levelname)s]: %(message)s',
                        datefmt='%m.%d.%Y %H:%M:%S',
                        level=logging.INFO)
    asyncio.run(main())
