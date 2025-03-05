from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from wwwpy.common.rpc2.transport import Transport


class TransportFake(Transport):

    def __init__(self):
        self.recv_buffer = []
        self.send_buffer = []
        self.send_sync_callback = lambda: None

        async def empty(): pass

        self.send_async_callback = empty

    def send_sync(self, payload: str | bytes):
        self.send_buffer.append(payload)
        self.send_sync_callback()

    async def send_async(self, payload: str | bytes):
        self.send_buffer.append(payload)
        await self.send_async_callback()

    def recv_sync(self) -> str | bytes:
        return self._consume()

    def _consume(self):
        if len(self.recv_buffer) == 0:
            raise Exception('Buffer is empty')
        return self.recv_buffer.pop(0)

    async def recv_async(self) -> str | bytes:
        return self._consume()


@dataclass
class PairedTransport:
    client: TransportFake = field(default_factory=lambda: TransportFake())
    server: TransportFake = field(default_factory=lambda: TransportFake())

    def __post_init__(self):
        self.client.recv_buffer = self.server.send_buffer
        self.client.send_buffer = self.server.recv_buffer


def test_client_send_sync():
    target = PairedTransport()

    target.client.send_sync('payload1')

    assert target.server.recv_sync() == 'payload1'


def test_loop_transport_empty():
    target = PairedTransport()
    with pytest.raises(Exception):
        target.server.recv_sync()

    with pytest.raises(Exception):
        target.client.recv_sync()
