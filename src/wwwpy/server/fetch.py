from __future__ import annotations

import asyncio
import urllib
import urllib.request
from typing import Any

from wwwpy.http import HttpResponse


async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    response = sync_fetch_response(url, method=method, data=data)
    assert isinstance(response.content, str)
    return response.content


def sync_fetch_response(url: str, method: str = 'GET', data: str | bytes = '') -> HttpResponse:
    def make_response(r: Any) -> HttpResponse:
        return HttpResponse(
            r.read().decode("utf-8"),
            r.headers.get_content_type()
        )

    if method != 'GET':
        if isinstance(data, str):
            data_bytes = bytes(data, 'utf8')
        else:
            data_bytes = data

        rq = urllib.request.Request(url, method=method, data=data_bytes)
        with urllib.request.urlopen(rq) as r:
            return make_response(r)
    else:
        with urllib.request.urlopen(url) as r:
            return make_response(r)


async def async_fetch_response(url: str, method: str = 'GET', data: str | bytes = '') -> HttpResponse:
    def make_response(r: Any) -> HttpResponse:
        return HttpResponse(
            r.read().decode("utf-8"),
            r.headers.get_content_type()
        )

    def fetch() -> HttpResponse:
        if method != 'GET':
            if isinstance(data, str):
                data_bytes = bytes(data, 'utf8')
            else:
                data_bytes = data

            rq = urllib.request.Request(url, method=method, data=data_bytes)
            with urllib.request.urlopen(rq) as r:
                return make_response(r)
        else:
            with urllib.request.urlopen(url) as r:
                return make_response(r)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fetch)
