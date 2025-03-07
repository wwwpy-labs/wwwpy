from __future__ import annotations

from typing import TypeVar, Union, Type

from wwwpy.common.rpc import serialization

T = TypeVar('T')


class EncoderDecoderType:
    buffer_type: Union[bytes, str]


class Encoder(EncoderDecoderType):
    buffer: bytes | str

    def encode(self, obj: any, cls: Type[T]):
        """Add the object to the encoder"""


class Decoder(EncoderDecoderType):
    def decode(self, cls: Type[T]) -> T:
        """Get the next object of the given type"""


class EncoderDecoder:
    def decoder(self, buffer: str | bytes) -> Decoder: raise NotImplementedError

    def encoder(self) -> Encoder: raise NotImplementedError


class JsonEncoder(Encoder):
    def __init__(self, sep: str):
        self._sep = sep
        self._buffer = []

    def encode(self, obj: any, cls: Type[T]):
        self._buffer.append(serialization.to_json(obj, cls))

    @property
    def buffer(self) -> str:
        return self._sep.join(self._buffer)


class JsonDecoder(Decoder):
    def __init__(self, buffer: str, sep: str):
        self._buffer = iter(buffer.split(sep))

    def decode(self, cls: Type[T]) -> T:
        item = next(self._buffer)
        return serialization.from_json(item, cls)


class JsonEncoderDecoder(EncoderDecoder):

    def __init__(self):
        self._sep = '\n'

    def decoder(self, buffer: str | bytes) -> Decoder:
        return JsonDecoder(buffer, sep=self._sep)

    def encoder(self) -> Encoder:
        return JsonEncoder(sep=self._sep)
