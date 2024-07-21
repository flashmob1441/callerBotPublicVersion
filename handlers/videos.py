import re
import logging

from aiogram import Router, F
from aiogram.types import Message

from downloaders.downloader import send_video
from utils.variables import BLACKLIST, URL_PATTERN

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text.contains('tiktok.com/'))
@router.message(F.text.contains('youtube.com/shorts/'))
@router.message(F.text.contains('instagram.com/reel/'))
async def command_videos_handler(message: Message) -> None:
    if message.from_user.id not in BLACKLIST:
        text = message.text
        url = re.search(URL_PATTERN, text).group('url')
        user = message.from_user.full_name
        logger.info(f'User {user} send video {url}')
        await send_video(message=message, url=url)
