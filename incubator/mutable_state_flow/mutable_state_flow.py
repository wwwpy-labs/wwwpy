import asyncio
from typing import Generic, TypeVar, AsyncIterator

T = TypeVar('T')


class MutableStateFlow(Generic[T]):
    def __init__(self, initial: T):
        self._value = initial
        self._subs: set[asyncio.Queue[T]] = set()
        self._lock = asyncio.Lock()

    @property
    def value(self) -> T:
        return self._value

    async def emit(self, value: T):
        async with self._lock:
            if value == self._value:
                return
            self._value = value
            for q in list(self._subs):
                if q.full():
                    q.get_nowait()
                await q.put(value)

    def try_emit(self, value: T, loop: asyncio.AbstractEventLoop | None = None) -> bool:
        if value == self._value:
            return True
        try:
            current = asyncio.get_running_loop()
        except RuntimeError:
            current = None
        target = loop or current or asyncio.get_event_loop()
        return target.run_until_complete(self.emit(value))

    def __aiter__(self) -> AsyncIterator[T]:
        q: asyncio.Queue[T] = asyncio.Queue(1)
        self._subs.add(q)

        async def gen():
            try:
                await q.put(self._value)
                while True:
                    yield await q.get()
            finally:
                self._subs.discard(q)

        return gen()
