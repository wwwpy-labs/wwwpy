from wwwpy.common.rpc.serializer import RpcRequest
from wwwpy.websocket import SendEndpoint


class Proxy:
    def __init__(self, module_name: str, send_endpoint: SendEndpoint):
        self.send_endpoint = send_endpoint
        self.module_name = module_name

    def dispatch(self, func_name: str, *args) -> None:
        rpc_request = RpcRequest.to_json(self.module_name, func_name, *args)
        self.send_endpoint.send(rpc_request)
