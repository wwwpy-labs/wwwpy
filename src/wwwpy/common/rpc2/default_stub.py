from __future__ import annotations

import types
from types import SimpleNamespace

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.stub import Stub
from wwwpy.common.rpc2.transport import Transport
from wwwpy.common.rpc2.typed_function import TypedFunction, get_typed_function
from wwwpy.exceptions import RemoteException, RemoteError


class DefaultStub(Stub):

    def __init__(self, transport: Transport, encdec: EncoderDecoder, module_name: str):
        self.namespace = SimpleNamespace()
        self._module_name = module_name
        self._transport = transport
        self._encdec = encdec

    def setup_functions(self, *functions: types.FunctionType) -> None:
        for f in functions:
            self._add_function(f)

    def setup_classes(self, *classes: type) -> None:
        ...

    def _add_function(self, f):
        ft = get_typed_function(f)

        def fun_sync(*args):
            return self.invoke_sync(ft, args)

        async def fun_async(*args):
            return await self.invoke_async(ft, args)

        fun = fun_async if ft.is_coroutine else fun_sync
        setattr(self.namespace, ft.func_name, fun)

    def invoke_sync(self, target_function: TypedFunction, args) -> any:
        send_buffer = self._encode_request(target_function, args)

        self._transport.send_sync(send_buffer)

        recv_buffer = self._transport.recv_sync()
        decode = self._decode_result(target_function, recv_buffer)
        return decode

    async def invoke_async(self, target_function: TypedFunction, args) -> any:
        send_buffer = self._encode_request(target_function, args)

        await self._transport.send_async(send_buffer)
        recv_buffer = await self._transport.recv_async()

        decode = self._decode_result(target_function, recv_buffer)
        return decode

    def _decode_result(self, target_function, recv_buffer):
        decoder = self._encdec.decoder(recv_buffer)
        status = decoder.decode(str)
        if status == 'ex':
            exception = decoder.decode(str)
            raise RemoteException(exception)
        elif status == 'ok':
            decode = decoder.decode(target_function.return_type)
            return decode
        else:
            raise RemoteError(f'Unknown status: `{status}`')

    def _encode_request(self, target_function, args):
        encoder = self._encdec.encoder()
        encoder.encode(self._module_name, str)
        encoder.encode(target_function.func_name, str)
        for arg, arg_type in zip(args, target_function.args_types):
            encoder.encode(arg, arg_type)
        send_buffer = encoder.buffer
        return send_buffer
