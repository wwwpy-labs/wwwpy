from __future__ import annotations

from typing import Any

from wwwpy.common.rpc.serializer import RpcRequest, RpcResponse
from wwwpy.common.rpc.v2.dispatcher import Dispatcher
from wwwpy.exceptions import RemoteException


# todo cleanup, this is 'mostly' used by the remote for the remote-to-server rpc(s)
#  but it's also used by the server tests. This should take care mostly about serialization/deserialization
#  and error handling, so we may completely abstract the transport (urllib, browser fetch etc etc)
#  and remove old tests and do new one for the new version
#  There are two counterparts to the dispatch, it's RpcRoute.dispatch() and setup_websocket().message()
class HybridDispatcher(Dispatcher):
    def __init__(self, module_name: str, rpc_url: str):
        self.rpc_url = rpc_url
        from wwwpy.common.fetch import async_fetch_str
        self.fetch = async_fetch_str
        self.module_name = module_name

    async def dispatch_async(self, func_name: str, *args) -> Any:
        rpc_request = RpcRequest.to_json(self.module_name, func_name, *args)
        json_response = await self.fetch(self.rpc_url, method='POST', data=rpc_request)
        response = RpcResponse.from_json(json_response)
        ex = response.exception
        if ex is not None and ex != '':
            raise RemoteException(ex)
        return response.result

    def dispatch_sync(self, func_name: str, *args) -> Any:
        rpc_request = RpcRequest.to_json(self.module_name, func_name, *args)
        import js
        xhr = js.XMLHttpRequest.new()
        xhr.open('POST', self.rpc_url, False)
        xhr.setRequestHeader('Content-Type', 'application/json')
        xhr.send(rpc_request)
        json_response = xhr.responseText
        response = RpcResponse.from_json(json_response)
        ex = response.exception
        if ex is not None and ex != '':
            raise RemoteException(ex)
        return response.result
