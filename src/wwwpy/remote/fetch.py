from js import fetch

import logging

logger = logging.getLogger(__name__)


async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    logger.debug(f'url={url}')
    logger.debug(f'method={method}')
    logger.debug(f'data=`{data}`')
    response = await fetch(url, method=method, body=data)
    text = await response.text()
    return text
