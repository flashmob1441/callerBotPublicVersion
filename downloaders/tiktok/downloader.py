from apis.api import request
from apis.request_methods import RequestMethod
from downloaders.tiktok.tiktok_slideshow_downloader import download_slideshow
from utils.api_urls import TIKTOK_API


async def get_download_video(video_url: str) -> str:
    params = {
        'url': video_url
    }
    json = await request(method=RequestMethod.GET, url=TIKTOK_API, params=params)
    data = json['data']
    images = data.get('images', None)
    if images is None:
        video = data['play']
    else:
        video = await download_slideshow(video_url)
    return video
