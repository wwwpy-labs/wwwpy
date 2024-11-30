from typing import Any

from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

UTF8 = "utf-8"


class AsgiHandler(WebSocketHandler):

    def initialize(self, asgi_app) -> None:
        super().initialize()
        self._asgi_app = asgi_app

    async def get(self, *args: Any, **kwargs: Any):
        if self.request.headers.get("Upgrade", "").lower() != "websocket":
            await self._handle_http_request(args, kwargs)
            return
        await super().get(*args, **kwargs)

    def open(self):
        logger.debug("open")


    async def post(self, *args: Any, **kwargs: Any):
        await self._handle_http_request(args, kwargs)

    async def _handle_http_request(self, *args: Any, **kwargs: Any):
        scope = {
            "type": self.request.protocol,
            "http_version": self.request.version,
            "path": self.request.path,
            "method": self.request.method,
            "query_string": self.request.query.encode(UTF8),
            "headers": self._collect_headers(),
            "client": (self.request.remote_ip, 0)
        }

        async def receive():
            return {'body': self.request.body, "type": "http.request", "more_body": False}

        async def send(data):
            if data['type'] == 'http.response.start':
                self.set_status(data['status'])
                self.clear_header("content-type")
                self.clear_header("server")
                self.clear_header("date")
                for h in data['headers']:
                    if len(h) == 2:
                        self.add_header(h[0].decode(UTF8), h[1].decode(UTF8))
            elif data['type'] == 'http.response.body':
                self.write(data['body'])
            else:
                raise RuntimeError(
                    f"Unsupported response type \"{data['type']}\" for asgi app")

        await self._asgi_app(scope, receive, send)

    def _collect_headers(self):
        headers = []
        for k in self.request.headers:
            for v in self.request.headers.get_list(k):
                headers.append((k.encode(UTF8).lower(), v.encode(UTF8)))
        return headers
