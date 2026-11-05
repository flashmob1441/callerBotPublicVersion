import re
import logging

from aiogram import Router, F
from aiogram.types import Message

from downloaders.downloader import send_video
from utils.throttle import allow
from utils.variables import BLACKLIST, URL_PATTERN

logger = logging.getLogger(__name__)

VIDEO_COOLDOWN = 10  # seconds per user

router = Router()


@router.message(F.text.contains('tiktok.com/'))
@router.message(F.text.contains('youtube.com/shorts/'))
@router.message(F.text.contains('instagram.com/reel/'))
@router.message(F.text.contains('xhslink.com'))
async def command_videos_handler(message: Message) -> None:
    if message.from_user and message.from_user.id in BLACKLIST:
        return
    match = re.search(URL_PATTERN, message.text)
    if match is None:
        return
    if message.from_user and not allow(('video', message.from_user.id), VIDEO_COOLDOWN):
        return
    url = match.group('url')
    user = message.from_user.full_name if message.from_user else message.chat.full_name
    logger.info(f'User {user} send video {url}')
    await send_video(message=message, url=url)
