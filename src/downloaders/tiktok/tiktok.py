from utils.api_urls import TIKTOK_API
from apis.api import request, RequestMethod
from downloaders.tiktok.slideshow_downloader import download_slideshow


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
        video = await download_slideshow(data=data)
    return video
