import asyncio
from functools import partial

from downloaders.tiktok import tiktok
from downloaders.ytdlp import get_download_url

HEAVY_TASKS = asyncio.Semaphore(2)  # ffmpeg / yt-dlp: max concurrent downloads

DOWNLOADERS = {
    "tiktok": tiktok.get_download_video,
    "instagram": partial(
        get_download_url,
        ie_key="Instagram",
        pick=lambda f: f.get("ext") == "mp4" and "dash" not in f.get("format_id", ""),
    ),
    "youtube": partial(
        get_download_url,
        ie_key="Youtube",
        pick=lambda f: f.get("ext") == "mp4",
        extra_opts={
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                    "skip": ["hls", "dash", "translated_subs"],
                }
            }
        },
    ),
    "rednote": partial(
        get_download_url,
        pick=lambda f: f.get("ext") == "mp4" and "direct" in f.get("format_id", ""),
    ),
}


async def download(source: str, url: str) -> str | None:
    """Возвращает http-ссылку или путь к локальному файлу (или None)."""
    async with HEAVY_TASKS:
        return await DOWNLOADERS[source](url)
