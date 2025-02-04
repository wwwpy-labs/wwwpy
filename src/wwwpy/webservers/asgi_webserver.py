from typing import Callable, Awaitable

from wwwpy.common.asynclib import OptionalCoroutine
from wwwpy.http import HttpRoute
from wwwpy.server.asgi import routes_to_asgi_application, AsgiApplication
from wwwpy.webserver import Webserver, Route
from wwwpy.websocket import WebsocketRoute


class AsgiWebserver(Webserver):
    def __init__(self, start):
        super().__init__()
        self._start = start
        self.app = AsgiApplication()

    def _setup_route(self, route: Route):
        if isinstance(route, HttpRoute):
            self.app.http_route[route.path] = route
        elif isinstance(route, WebsocketRoute):
            self.app.websocket_route[route.path] = route
        else:
            raise Exception(f'Unknown route type: {type(route)}')

    async def _start_listen(self) -> None:
        await self._start(self)
