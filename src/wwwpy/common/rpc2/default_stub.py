from __future__ import annotations

import types
from types import SimpleNamespace

from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder
from wwwpy.common.rpc2.stub import Stub
from wwwpy.common.rpc2.transport import Transport
from wwwpy.common.rpc2.typed_function import TypedFunction, get_typed_function


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

        def fun(*args):
            return self.invoke_sync(ft, args)

        setattr(self.namespace, ft.func_name, fun)

    def invoke_sync(self, target_function: TypedFunction, args) -> any:
        encoder = self._encdec.encoder()
        encoder.encode(self._module_name, str)
        encoder.encode(target_function.func_name, str)
        for arg, arg_type in zip(args, target_function.args_types):
            encoder.encode(arg, arg_type)
        send_buffer = encoder.buffer

        self._transport.send_sync(send_buffer)

        recv_buffer = self._transport.recv_sync()
        decoder = self._encdec.decoder(recv_buffer)
        return decoder.decode(target_function.return_type)
