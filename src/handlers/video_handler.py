import logging
import os
import re

from aiogram import F, Router, md
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, Message, URLInputFile

from downloaders.downloader import download
from utils.config import BLACKLIST
from utils.throttle import allow
from utils.urls import get_source
from utils.variables import URL_PATTERN

logger = logging.getLogger(__name__)

VIDEO_COOLDOWN = 10  # seconds per user

router = Router()


@router.message(F.text.regexp(URL_PATTERN).as_("match"))
async def command_videos_handler(message: Message, match: re.Match) -> None:
    user_id = message.from_user.id if message.from_user else None
    if user_id in BLACKLIST:
        return
    url = match.group("url")
    source = get_source(url)
    if source is None:
        return
    if user_id and not allow(("video", user_id), VIDEO_COOLDOWN):
        return
    user = message.from_user.full_name if message.from_user else message.chat.full_name
    logger.info(f"User {user} send video {url}")

    video_path = None
    try:
        video_path = await download(source, url)
        if not video_path:
            raise ValueError("downloader returned no video")
        if video_path.startswith("http"):
            # ponytail: youtube/xhs ссылки Telegram сам не скачает, остальные отдаём как есть
            video = (
                URLInputFile(url=video_path)
                if ("videoplayback" in video_path or "xhscdn" in video_path)
                else video_path
            )
        else:
            video = FSInputFile(path=video_path)
        await message.answer_video(
            video=video,
            caption=md.quote(user or ""),
            supports_streaming=True,
            allow_sending_without_reply=True,
            disable_notification=True,
            parse_mode=ParseMode.MARKDOWN_V2,
        )
    except Exception:
        logger.exception(f"Failed to send video {url}")
    finally:
        if (
            video_path
            and not video_path.startswith("http")
            and os.path.exists(video_path)
        ):
            os.remove(video_path)
