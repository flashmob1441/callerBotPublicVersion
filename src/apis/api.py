import logging
from enum import Enum

from aiohttp import ClientSession, ClientTimeout

logger = logging.getLogger(__name__)


class RequestMethod(Enum):
    GET = "GET"
    POST = "POST"


HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en",
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/110.0.0.0 Safari/537.36",
}

_session: ClientSession | None = None


def _get_session() -> ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = ClientSession(headers=HEADERS, timeout=ClientTimeout(total=30))
    return _session


async def close_session() -> None:
    if _session is not None and not _session.closed:
        await _session.close()


async def request(
    method: RequestMethod,
    url: str,
    params: dict | None = None,
    json: dict | None = None,
    headers: dict | None = None,
) -> dict:
    async with _get_session().request(
        method=method.value, url=url, params=params, json=json, headers=headers
    ) as response:
        response.raise_for_status()
        return await response.json()
