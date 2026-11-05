import asyncio
from collections.abc import Callable

import yt_dlp


async def get_download_url(
    video_url: str,
    pick: Callable[[dict], bool],
    ie_key: str | None = None,
    extra_opts: dict | None = None,
) -> str | None:
    """Возвращает прямую ссылку первого формата, для которого pick(format) истинно."""
    opts = {
        "format": "bestvideo+bestaudio/best",
        "socket_timeout": 30,
        **(extra_opts or {}),
    }

    def extract_info() -> dict:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(video_url, ie_key=ie_key, download=False)

    info = await asyncio.to_thread(extract_info)
    return next((f["url"] for f in info.get("formats", []) if pick(f)), None)
