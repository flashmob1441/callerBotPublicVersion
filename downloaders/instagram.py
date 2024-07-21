from bs4 import BeautifulSoup

from apis.api import request
from apis.request_methods import RequestMethod
from utils.api_urls import INSTAGRAM_API


async def get_download_url(video_url: str) -> str:
    params = {
        'q': video_url
    }
    json = await request(method=RequestMethod.GET, url=INSTAGRAM_API, params=params)
    data = json['data']
    soup = BeautifulSoup(data, 'lxml')
    return soup.find_all('a', class_='abutton is-success is-fullwidth btn-premium mt-3')[1]['href']
