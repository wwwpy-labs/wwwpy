from __future__ import annotations

import logging

from wwwpy.common.escapelib import escape_string
from wwwpy.common.rpc2.transport import Transport

logger = logging.getLogger(__name__)

try:
    import js


    class RemoteHttpTransport(Transport):
        def __init__(self, rpc_url: str):
            self.rpc_url = rpc_url
            self.response = None

        def _buf(self, payload: str | bytes):
            if self.response:
                raise Exception('Cannot send twice with this implementation')
            self.response = payload

        def _consume(self):
            if self.response is None:
                raise Exception('Cannot consume before sending')
            response = self.response
            self.response = None
            return response

        async def send_async(self, payload: str | bytes):
            logger.debug(f'send_async payload: `{escape_string(payload)}`')
            json_response = await js.fetch(self.rpc_url, method='POST', body=payload)
            text = await json_response.text()
            # response = RpcResponse.from_json(json_response)
            # ex = response.exception
            # if ex is not None and ex != '':
            #     raise RemoteException(ex)
            self._buf(text)

        def send_sync(self, payload: bytes):
            # rpc_request = RpcRequest.to_json(self.module_name, func_name, *args)
            # import js
            xhr = js.XMLHttpRequest.new()
            xhr.open('POST', self.rpc_url, False)
            xhr.setRequestHeader('Content-Type', 'application/json')
            xhr.send(payload)
            json_response = xhr.responseText
            # response = RpcResponse.from_json(json_response)
            # ex = response.exception
            # if ex is not None and ex != '':
            #     raise RemoteException(ex)
            self._buf(json_response)

        def recv_sync(self) -> bytes:
            return self._consume()

        async def recv_async(self) -> str | bytes:
            return self._consume()


    class ServerHttpTransport(Transport):
        pass
except:
    class ServerHttpTransport(Transport):
        def __init__(self, request: str | bytes):
            self._recv = request
            self.response = None

        def _buf(self, payload: str | bytes):
            if self.response:
                raise Exception('Cannot send twice with this implementation')
            self.response = payload

        def _consume_recv(self):
            if self._recv is None:
                raise Exception('Cannot consume before sending')
            response = self._recv
            self._recv = None
            return response

        def recv_sync(self) -> bytes:
            return self._consume_recv()

        async def recv_async(self) -> str | bytes:
            return self._consume_recv()

        def send_sync(self, payload: bytes):
            self._buf(payload)

        async def send_async(self, payload: str | bytes):
            self._buf(payload)


    class RemoteHttpTransport(Transport):
        ...
