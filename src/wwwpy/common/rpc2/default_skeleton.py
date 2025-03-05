from __future__ import annotations

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.skeleton import Skeleton
from wwwpy.common.rpc2.transport import Transport
from wwwpy.common.rpc2.typed_function import get_typed_function


def _get_args_types(func): ...


def _get_return_type(func): ...


class DefaultSkeleton(Skeleton):
    def __init__(self, transport: Transport, encdec: EncoderDecoder, allowed_modules: set[str]):
        self._transport = transport
        self._encdec = encdec
        self._allowed_modules = allowed_modules

    def invoke_sync(self):
        recv_buffer = self._transport.recv_sync()
        args, func, target_function = self._decode(recv_buffer)

        result = func(*args)

        send_buffer = self._encode(target_function, result)
        self._transport.send_sync(send_buffer)

    async def invoke_async(self):
        recv_buffer = await self._transport.recv_async()
        args, func, target_function = self._decode(recv_buffer)

        result = await func(*args)

        send_buffer = self._encode(target_function, result)
        await self._transport.send_async(send_buffer)

    def _decode(self, recv_buffer):
        decoder = self._encdec.decoder(recv_buffer)
        module_name = decoder.decode(str)
        if module_name not in self._allowed_modules:
            raise Exception(f'Not allowed module: {module_name}')
        func_name = decoder.decode(str)
        import importlib
        module = importlib.import_module(module_name)
        func = getattr(module, func_name)
        target_function = get_typed_function(func)
        args = []
        for arg_type in target_function.args_types:
            args.append(decoder.decode(arg_type))
        return args, func, target_function

    def _encode(self, target_function, result):
        encoder = self._encdec.encoder()
        encoder.encode(result, target_function.return_type)
        send_buffer = encoder.buffer
        return send_buffer
