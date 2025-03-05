from __future__ import annotations


class Transport:

    def send_sync(self, payload: str | bytes): raise NotImplementedError

    async def send_async(self, payload: str | bytes): raise NotImplementedError

    def recv_sync(self) -> str | bytes: raise NotImplementedError

    async def recv_async(self) -> str | bytes: raise NotImplementedError
