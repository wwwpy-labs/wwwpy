from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Union, Type

T = TypeVar('T')


class Buffer:
    buffer_type: Union[bytes, str]
    buffer: bytes | str
    """Set or get the buffer"""


class Encoder(Buffer):
    def reset_buffer(self):
        pass

    def add(self, obj: any, cls: Type[T]):
        """Add the object to the encoder"""


class Decoder(Buffer):
    def next(self, cls: Type[T]) -> T:
        """Get the next object of the given type"""


@dataclass
class EncoderDecoder:
    encoder: Type[Encoder]
    decoder: Type[Decoder]


class JsonEncoder(Encoder):
    buffer_type = str

    def reset_buffer(self):
        raise NotImplementedError

    def add(self, obj: any, cls: Type[T]):
        raise NotImplementedError

    @property
    def buffer(self) -> str:
        raise NotImplementedError

    @buffer.setter
    def buffer(self, value: str):
        raise 'Cannot set buffer in Encoder'


class JsonDecoder(Decoder):
    buffer_type = str

    def next(self, cls: Type[T]) -> T:
        raise NotImplementedError

    @property
    def buffer(self) -> str:
        raise NotImplementedError

    @buffer.setter
    def buffer(self, value: str):
        raise 'Cannot set buffer in Decoder'


json_encoder_decoder = EncoderDecoder(encoder=Encoder, decoder=Decoder)


def json_encoder_decoder_def() -> EncoderDecoder:
    return json_encoder_decoder
