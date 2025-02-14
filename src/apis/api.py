import asyncio
import logging

from enum import Enum
from aiohttp import ClientSession

logger = logging.getLogger(__name__)


class RequestMethod(Enum):
    GET = 'GET'
    POST = 'POST'


HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/110.0.0.0 Safari/537.36'
}


async def request(method: RequestMethod,
                  url: str,
                  params: dict = None,
                  json: dict = None,
                  headers: dict = None) -> dict:
    request_headers = HEADERS | headers if headers is not None else HEADERS
    json_result = {}
    try:
        async with ClientSession(headers=request_headers) as session:
            async with session.request(method=method.value,
                                       url=url,
                                       params=params,
                                       json=json) as response:
                if response.status == 200:
                    json_result = await response.json()
                else:
                    logger.error(f'Status code error {url} - {response.status}')
        await asyncio.sleep(0.25)
    except Exception as e:
        logger.error(e)
    finally:
        return json_result
