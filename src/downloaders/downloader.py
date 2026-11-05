import os
import logging

from aiogram import md
from aiogram.enums import ParseMode
from aiogram.types import Message, URLInputFile, FSInputFile

from downloaders.tiktok import tiktok
from downloaders import youtube_shorts, instagram, rednote
from utils.urls import get_source

logger = logging.getLogger(__name__)

DOWNLOADERS = {
    'tiktok': tiktok.get_download_video,
    'instagram': instagram.get_download_url,
    'youtube': youtube_shorts.get_download_url,
    'rednote': rednote.get_download_url,
}


async def send_video(message: Message, url: str) -> None:
    source = get_source(url)
    if source is None:
        logger.warning(f'Unsupported url {url}')
        return
    video_path = None
    try:
        video_path = await DOWNLOADERS[source](url)
        if not video_path:
            raise ValueError('downloader returned no video')
        if video_path.startswith('http'):
            if 'videoplayback' in video_path or 'xhscdn' in video_path:
                video = URLInputFile(url=video_path)
            else:
                video = video_path
        else:
            video = FSInputFile(path=video_path)
        user = message.from_user.full_name if message.from_user else message.chat.full_name
        await message.answer_video(video=video,
                                   caption=md.quote(user or ''),
                                   supports_streaming=True,
                                   allow_sending_without_reply=True,
                                   disable_notification=True,
                                   parse_mode=ParseMode.MARKDOWN_V2)
    except Exception:
        logger.exception(f'Failed to send video {url}')
    finally:
        if video_path and not video_path.startswith('http') and os.path.exists(video_path):
            os.remove(video_path)
