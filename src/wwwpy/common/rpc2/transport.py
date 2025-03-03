from __future__ import annotations


class Transport:

    def send_sync(self, payload: str | bytes) -> str | bytes: ...

    async def send_async(self, payload: str | bytes) -> str | bytes: ...
