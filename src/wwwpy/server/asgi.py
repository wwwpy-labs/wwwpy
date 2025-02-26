from __future__ import annotations

from wwwpy.common.asynclib import OptionalCoroutine
from wwwpy.common.rpc.serializer import RpcRequest
from wwwpy.http import HttpRoute, HttpRequest, HttpResponse
from wwwpy.webserver import Route
from wwwpy.websocket import WebsocketRoute, WebsocketEndpoint, ListenerProtocol


# Route = Union[HttpRoute, WebsocketRoute]

def routes_to_asgi_application(*routes: Route):
    return AsgiApplication(routes)


class AsgiApplication:
    def __init__(self, *routes: Route):
        def _g(type_):
            return _groupby_to_dict(filter(lambda r: isinstance(r, type_), routes), lambda i: i.path)

        self.http_route: dict[str, HttpRoute] = _g(HttpRoute)
        self.websocket_route: dict[str, WebsocketRoute] = _g(WebsocketRoute)

        self._scopes = {
            'http': self._scope_http,
            'websocket': self._scope_websocket,
            'lifespan': self._scope_lifespan,
        }

    async def __call__(self, scope, receive, send):
        func = self._scopes.get(scope['type'], None)
        if func is None:
            return
        await func(scope, receive, send)  # noqa

    async def _scope_lifespan(self, scope, receive, send):
        pass

    async def _scope_http(self, scope, receive, send):
        route = self.http_route.get(scope['path'], None)
        if route is None:
            return
        method = scope['method']
        headers = dict(scope['headers'])
        content_type = headers.get('content-type', None)
        body = await _all_body(receive)
        # todo (?) intercept content type to correctly transform body bytes to str if needed
        http_request = HttpRequest(method, body, content_type)

        def resp_callback(resp: HttpResponse) -> OptionalCoroutine:
            async def future():
                await send({'type': 'http.response.start', 'status': 200,
                            'headers': [[b'content-type', resp.content_type.encode()], ], })
                await send({'type': 'http.response.body', 'body': resp.content.encode(), })

            return future()

        res = route.callback(http_request, resp_callback)
        if res:
            await res

    async def _scope_websocket(self, scope, receive, send):
        route = self.websocket_route.get(scope['path'], None)
        if route is None:
            return

        # send_text = lambda t: send({'type': 'websocket.send', 'text': t})
        async def send_text(t):
            await send({'type': 'websocket.send', 'text': t})

        await send({'type': 'websocket.accept'})

        endpoint = _AsgiWebsocketEndpoint(lambda m: send_text(m))
        route.on_connect(endpoint)

        while True:
            message = await receive()
            if message['type'] == 'websocket.receive':
                await endpoint.on_message(message.get('text'))
            elif message['type'] == 'websocket.disconnect':
                break


def _groupby_to_dict(iterable, key) -> dict:
    result = dict()
    for item in iterable:
        k = key(item)
        array = result.get(k, None)
        if array is None:
            array = []
            result[k] = array
        array.append(item)
    return result


async def _all_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body


class _AsgiWebsocketEndpoint(WebsocketEndpoint):
    def __init__(self, send: ListenerProtocol):
        self._send = send
        self._listener: ListenerProtocol | None = None

    def add_listener(self, listener: ListenerProtocol) -> None:
        if self._listener is not None:
            raise Exception('Only one listener is allowed')
        self._listener = listener

    # part to be called by user code to send a outgoing message
    def send(self, message: str | bytes | None) -> OptionalCoroutine:
        return self._send(message)

    # parte to be used by IO implementation to be called to notify incoming messages
    def on_message(self, message: str | bytes | None) -> OptionalCoroutine:
        if self._listener is not None:
            return self._listener(message)

    def dispatch(self, module: str, func_name: str, *args) -> OptionalCoroutine:
        j = RpcRequest.to_json(module, func_name, *args)
        return self.send(j)
