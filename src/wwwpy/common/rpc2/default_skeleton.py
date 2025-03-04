from __future__ import annotations

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.skeleton import Skeleton
from wwwpy.common.rpc2.transport import Transport
from wwwpy.common.rpc2.typed_function import get_typed_function


def _get_args_types(func): ...


def _get_return_type(func): ...


class DefaultSkeleton(Skeleton):
    def __init__(self, transport: Transport, encdec: EncoderDecoder):
        self._transport = transport
        self._encdec = encdec

    def invoke_sync(self):
        recv_buffer = self._transport.recv_sync()
        decoder = self._encdec.decoder(recv_buffer)
        module_name = decoder.decode(str)
        func_name = decoder.decode(str)

        import importlib
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)

        target_function = get_typed_function(func)
        args = []
        for arg_type in target_function.args_types:
            args.append(decoder.decode(arg_type))

        result = func(*args)

        encoder = self._encdec.encoder()
        encoder.encode(result, target_function.return_type)
        send_buffer = encoder.buffer
        self._transport.send_sync(send_buffer)

    async def invoke_async(self):
        return await super().invoke_async()
