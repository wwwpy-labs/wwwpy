from __future__ import annotations

import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from types import FunctionType

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.skeleton import Skeleton
from wwwpy.common.rpc2.transport import Transport
from wwwpy.common.rpc2.typed_function import get_typed_function, TypedFunction
from wwwpy.unasync import unasync


def _get_args_types(func): ...


def _get_return_type(func): ...


class DefaultSkeleton(Skeleton):
    def __init__(self, transport: Transport, encdec: EncoderDecoder, allowed_modules: set[str]):
        self._transport = transport
        self._encdec = encdec
        self._allowed_modules = allowed_modules

    def invoke_tobe_fixed(self):
        recv_buffer = self._transport.recv_sync()
        args, func, target_function = self._decode_request(recv_buffer)

        if target_function.is_coroutine:
            @unasync
            async def func_async(*args):
                with _catch() as r:
                    r.value = await func(*args)
                return r

            r = func_async(*args)
        else:
            with _catch() as r:
                r.value = func(*args)

        send_buffer = self._encode_result(target_function, r)
        self._transport.send_sync(send_buffer)

    def invoke_sync(self):
        # raise Exception('Not implemented - see invoke_tobe_fixed')
        recv_buffer = self._transport.recv_sync()
        args, func, target_function = self._decode_request(recv_buffer)

        with _catch() as r:
            r.value = func(*args)

        send_buffer = self._encode_result(target_function, r)
        self._transport.send_sync(send_buffer)

    async def invoke_async(self):
        # raise Exception('Not implemented - see invoke_tobe_fixed')
        recv_buffer = await self._transport.recv_async()
        args, func, target_function = self._decode_request(recv_buffer)

        with _catch() as r:
            r.value = await func(*args)

        send_buffer = self._encode_result(target_function, r)
        await self._transport.send_async(send_buffer)

    def _decode_request(self, recv_buffer) -> tuple[list[any], FunctionType, TypedFunction]:
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

    def _encode_result(self, target_function, result: _Result):
        encoder = self._encdec.encoder()
        if result.exception_str:
            encoder.encode('ex', str)
            encoder.encode(result.exception_str, str)
        else:
            encoder.encode('ok', str)
            encoder.encode(result.value, target_function.return_type)
        send_buffer = encoder.buffer
        return send_buffer


@dataclass
class _Result:
    value: any = None
    exception_str: str | None = None


@contextmanager
def _catch(*args, **kwds):
    r = _Result()
    try:
        yield r
    except Exception as e:
        r.exception_str = traceback.format_exc()
