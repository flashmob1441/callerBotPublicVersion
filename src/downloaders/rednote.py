import yt_dlp
import asyncio
import logging

logger = logging.getLogger(__name__)


async def get_download_url(video_url: str) -> str | None:
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best'
    }

    def extract_info():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(video_url, download=False)

    info: dict = await asyncio.to_thread(extract_info)

    for video_format in info.get('formats', []):
        if video_format.get('ext') == 'mp4' and 'direct' in video_format.get('format_id'):
            return video_format.get('url')

    return None
