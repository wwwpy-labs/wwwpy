from typing import Any
import asyncio
from tornado.websocket import WebSocketHandler
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

UTF8 = "utf-8"


class ASGIHandler(WebSocketHandler):

    def initialize(self, asgi_app) -> None:
        super().initialize()
        self._asgi_app = asgi_app

    async def get(self, *args: Any, **kwargs: Any):
        if self.request.headers.get("Upgrade", "").lower() != "websocket":
            await self._handle_http_request(args, kwargs)
            return
        await super().get(*args, **kwargs)  # continue as a real WebSocketHandler, thus to self.open()

    def open(self):
        logger.debug("WebSocket connection opened")
        self.receive_queue = asyncio.Queue()
        asyncio.create_task(self._run_asgi_app())

    async def _run_asgi_app(self):
        scope = {
            "type": "websocket",
            "asgi": {"version": "3.0"},
            "http_version": self.request.version,
            "scheme": self.request.protocol,
            "path": self.request.path,
            "raw_path": self.request.path.encode(UTF8),
            "query_string": self.request.query.encode(UTF8),
            "headers": self._collect_headers(),
            "client": (self.request.remote_ip, 0),
            "server": self.request.host,
            "subprotocols": self.request.headers.get_list("Sec-WebSocket-Protocol"),
        }

        async def receive():
            return await self.receive_queue.get()

        async def send(message):
            message_type = message.get('type')
            if message_type == 'websocket.send':
                if 'text' in message:
                    await self.write_message(message['text'])
                elif 'bytes' in message:
                    await self.write_message(message['bytes'], binary=True)
            elif message_type == 'websocket.close':
                code = message.get('code', 1000)
                reason = message.get('reason', '')
                await self.close(code=code, reason=reason)
            else:
                logger.error(f"Unsupported ASGI message type: {message_type}")

        try:
            await self._asgi_app(scope, receive, send)
        except Exception as e:
            logger.error(f"Error in ASGI application: {e}")
            await self.close()

    def on_message(self, message):
        asyncio.create_task(self._queue_message(message))

    async def _queue_message(self, message):
        await self.receive_queue.put({'type': 'websocket.receive',
                                      'bytes' if isinstance(message, bytes) else 'text': message})

    def on_close(self):
        logger.debug("WebSocket connection closed")
        asyncio.create_task(self._queue_disconnect())

    async def _queue_disconnect(self):
        await self.receive_queue.put({'type': 'websocket.disconnect'})

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
            "client": (self.request.remote_ip, 0),
            "server": self.request.host,
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
                    f"Unsupported response type \"{data['type']}\" for ASGI app")

        await self._asgi_app(scope, receive, send)

    def _collect_headers(self):
        headers = []
        for k in self.request.headers:
            for v in self.request.headers.get_list(k):
                headers.append((k.encode(UTF8).lower(), v.encode(UTF8)))
        return headers
