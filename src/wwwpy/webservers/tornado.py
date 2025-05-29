from __future__ import annotations

from threading import Thread
from typing import Awaitable, Union
from typing import Optional

import tornado
import tornado.web
from tornado import websocket
from tornado.ioloop import IOLoop

from wwwpy.http import HttpRoute, HttpRequest
from ..webserver import Webserver, Route
from ..websocket import WebsocketRoute, WebsocketEndpointIO


class WsTornado(Webserver):
    ioloop: IOLoop = None

    def __init__(self):
        super().__init__()
        self.app = tornado.web.Application()
        self.thread: Optional[Thread] = None

    def _setup_route(self, route: Route):
        if isinstance(route, WebsocketRoute):
            self.app.add_handlers(r".*", [(route.path, _WebsocketHandler, dict(route=route, server=self))])
        else:
            self.app.add_handlers(r".*", [(route.path, TornadoHandler, dict(route=route))])

    def _start_listen(self):
        def run():
            self.app.listen(self.port, self.host)
            self.ioloop = IOLoop.current()
            # asyncio.set_event_loop(self.ioloop.asyncio_loop)
            self.ioloop.start()

        self.thread = Thread(target=run, daemon=True)
        self.thread.start()


class TornadoHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        self.route: Route = None
        self._serve = None
        super().__init__(*args, **kwargs)

    def initialize(self, route: HttpRoute) -> None:
        self.route = route
        if not isinstance(route, HttpRoute):
            raise Exception(f'Unknown route type: {type(route)}')

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self):
        """/OPTIONS handler for preflight CORS checks."""
        self.set_status(204)
        self.finish()

    async def get(self) -> None:
        await self._serve_std('GET')

    async def post(self) -> None:
        await self._serve_std('POST')

    async def _serve_std(self, verb: str):
        body = self.request.body
        request = HttpRequest(verb, body, self.request.headers.get('Content-Type', ''))

        def response_fun(response):
            self.set_default_headers()
            self.set_header("Content-Type", response.content_type)
            return self.write(response.content)

        res = self.route.callback(request, response_fun)
        if res:
            await res

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        raise_exception(self)


class _WebsocketHandler(websocket.WebSocketHandler):
    route: WebsocketRoute = None
    server: WsTornado = None
    endpoint: WebsocketEndpointIO = None

    def initialize(self, route: WebsocketRoute, server: WsTornado) -> None:
        self.route = route
        self.server = server

    # def check_origin(self, origin):
    #     return True

    def open(self):
        self.endpoint = WebsocketEndpointIO(self._on_send)
        self.route.on_connect(self.endpoint)

    def on_message(self, message: Union[str, bytes]) -> Optional[Awaitable[None]]:
        self.endpoint.on_message(message)

    def _on_send(self, data: str | bytes | None):
        if data is None:
            self.close()
        else:
            self.server.ioloop.asyncio_loop.call_soon_threadsafe(self.write_message, data)

    def on_close(self):
        self.endpoint.on_message(None)


def raise_exception(self: TornadoHandler):
    print("=" * 60)
    print(f'exc! {self.route}')
    raise Exception(self)
