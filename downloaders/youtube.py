from urllib.parse import urlparse

from apis.api import request
from apis.request_methods import RequestMethod
from utils.api_urls import YOUTUBE_API


async def get_download_url(video_url: str) -> str:
    video_id = urlparse(video_url).path.strip('/').split('/')[-1]
    request_url = YOUTUBE_API + video_id
    json = await request(method=RequestMethod.GET, url=request_url)
    url = json['qualities'][0]['url']
    return url
