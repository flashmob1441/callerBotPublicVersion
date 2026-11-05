import asyncio
import logging
import os
import uuid

import yt_dlp

from apis.api import RequestMethod, request
from downloaders.tiktok.slideshow_downloader import RESULTS_DIR, download_slideshow
from utils.api_urls import TIKTOK_API

logger = logging.getLogger(__name__)


async def get_download_video(video_url: str) -> str:
    try:
        json = await request(
            method=RequestMethod.GET, url=TIKTOK_API, params={"url": video_url}
        )
        if json.get("code") != 0 or not json.get("data"):
            raise ValueError(f"tikwm error: {json.get('msg')}")
    except Exception as e:  # noqa: BLE001 - любой сбой tikwm => фолбэк на yt-dlp
        logger.warning(f"tikwm failed for {video_url} ({e!r}), falling back to yt-dlp")
        return await download_with_ytdlp(video_url)

    data = json["data"]
    if data.get("images") is None:
        return data["play"]
    return await download_slideshow(data=data)


async def download_with_ytdlp(video_url: str) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": os.path.join(RESULTS_DIR, f"yt-{uuid.uuid4().hex[:8]}.%(ext)s"),
        "socket_timeout": 30,
        "quiet": True,
    }

    def download() -> str:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.prepare_filename(ydl.extract_info(video_url, download=True))

    return await asyncio.to_thread(download)
