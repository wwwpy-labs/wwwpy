from __future__ import annotations


class Skeleton:
    def invoke_sync(self): raise NotImplementedError

    async def invoke_async(self): raise NotImplementedError
