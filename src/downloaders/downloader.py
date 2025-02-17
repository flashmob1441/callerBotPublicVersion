import os
import logging

from aiogram import md
from aiogram.enums import ParseMode
from aiogram.types import Message, URLInputFile, FSInputFile

from downloaders.tiktok import tiktok
from downloaders import youtube_shorts, instagram, rednote

logger = logging.getLogger(__name__)


async def send_video(message: Message, url: str) -> None:
    user = message.from_user.full_name
    video_path = await get_video(url)
    if 'http' in video_path:
        if 'videoplayback' in video_path or 'xhscdn' in video_path:
            video = URLInputFile(url=video_path)
        else:
            video = video_path
    elif 'mp4' in video_path:
        video = FSInputFile(path=video_path)
    else:
        logger.error(f'Send wrong url {url}')
        return
    try:
        await message.answer_video(video=video,
                                   caption=md.quote(user),
                                   supports_streaming=True,
                                   allow_sending_without_reply=True,
                                   disable_notification=True,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(e)
    finally:
        if 'mp4' in video_path and os.path.exists(video_path):
            os.remove(video_path)


async def get_video(url: str) -> str | list[str]:
    result = ''
    if 'tiktok.com' in url:
        result = await tiktok.get_download_video(video_url=url)
    elif 'instagram.com' in url:
        result = await instagram.get_download_url(video_url=url)
    elif 'youtube.com/shorts' in url:
        result = await youtube_shorts.get_download_url(video_url=url)
    elif 'xhslink.com' in url:
        result = await rednote.get_download_url(video_url=url)
    return result
