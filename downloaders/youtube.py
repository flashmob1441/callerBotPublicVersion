import re

from aiohttp import ClientSession
from urllib.parse import urlparse

from apis.api import request
from apis.request_methods import RequestMethod
from utils.api_urls import YOUTUBE_API


async def get_download_url(video_url: str) -> str:
    token = await get_token()
    headers = {
        'X-Rapidapi-Host': 'yt-api.p.rapidapi.com',
        'X-Rapidapi-Key': token
    }
    video_id = urlparse(video_url).path.strip('/').split('/')[-1]
    params = {
        'id': video_id
    }
    json = await request(method=RequestMethod.GET, url=YOUTUBE_API, headers=headers, params=params)
    url = json['formats'][0]['url']
    return url


async def get_token() -> str:
    token_pattern = r'[a-z0-9]{50}'
    url = 'https://www.ytsavepro.com/_next/static/chunks/325-a865888116ca371d.js'
    async with ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
    return re.findall(token_pattern, text)[0].strip()
