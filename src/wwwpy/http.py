from typing import NamedTuple, Callable, Union
# todo rename this in httplib (otherwise it crash jetbrains debug mode)
from wwwpy.common.asynclib import OptionalCoroutine


class HttpRequest(NamedTuple):
    method: str
    content: Union[str, bytes]
    content_type: str


class HttpResponse(NamedTuple):
    content: Union[str, bytes]
    content_type: str

    @staticmethod
    def application_zip(content: bytes) -> 'HttpResponse':
        content_type = 'application/zip, application/octet-stream, application/x-zip-compressed, multipart/x-zip'
        return HttpResponse(content, content_type)

    @staticmethod
    def text_html(content: str) -> 'HttpResponse':
        return HttpResponse(content, 'text/html')


class HttpRoute(NamedTuple):
    path: str
    callback: Callable[[HttpRequest, Callable[[HttpResponse], OptionalCoroutine]], OptionalCoroutine]
