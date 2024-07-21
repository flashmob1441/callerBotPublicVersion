import os
import logging

from aiogram import md
from aiogram.types import Message, URLInputFile, FSInputFile

from downloaders import youtube, instagram
from downloaders.tiktok import downloader

logger = logging.getLogger(__name__)


async def send_video(message: Message, url: str) -> None:
    user = message.from_user.full_name
    video_path = await get_video(url)
    if 'http' in video_path:
        video = URLInputFile(url=video_path)
    elif 'mp4' in video_path:
        video = FSInputFile(path=video_path)
    else:
        logger.error(f'Send wrong url {url}')
        return
    await message.answer_video(video=video,
                               caption=md.quote(user),
                               supports_streaming=True,
                               allow_sending_without_reply=True,
                               disable_notification=True)
    if 'mp4' in video_path and os.path.exists(video_path):
        os.remove(video_path)


async def get_video(url: str) -> str:
    result = ''
    if 'tiktok.com' in url:
        result = await downloader.get_download_video(video_url=url)
    elif 'instagram.com/reel/' in url:
        result = await instagram.get_download_url(video_url=url)
    elif 'youtube.com/shorts' in url:
        result = await youtube.get_download_url(video_url=url)
    return result
