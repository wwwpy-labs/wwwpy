from js import fetch, console

from wwwpy.common.fetch_debug import fetch_debug

# logger = logging.getLogger(__name__)
logger = console  # if log redirect is active, it will create an infinite loop because


async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    logger.debug(__name__ + ' ' + fetch_debug(url, method, data))
    response = await fetch(url, method=method, body=data)
    text = await response.text()
    return text
