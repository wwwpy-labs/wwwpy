from __future__ import annotations

import logging
from enum import Enum
from typing import NamedTuple, Protocol, List, Iterator

from wwwpy.common.asynclib import OptionalCoroutine
from wwwpy.common.rpc.serializer import RpcRequest

logger = logging.getLogger(__name__)


class WebsocketRoute(NamedTuple):
    path: str
    on_connect: Callable[[WebsocketEndpoint], None]


class Change(Enum):
    add = 'add'
    remove = 'remove'


class PoolEvent(NamedTuple):
    change: Change
    endpoint: WebsocketEndpoint
    pool: WebsocketPool

    @property
    def add(self) -> bool:
        return self.change == Change.add

    @property
    def remove(self) -> bool:
        return self.change == Change.remove


class PoolChangeCallback(Protocol):
    def __call__(self, change: PoolEvent) -> None: ...


class WebsocketPool:

    def __init__(self, route: str):
        self.clients: list[WebsocketEndpoint] = []
        self.http_route = WebsocketRoute(route, self._on_connect)
        self.on_before_change: List[PoolChangeCallback] = []
        self.on_after_change: List[PoolChangeCallback] = []

    def _notify_change(self, change: PoolEvent, listeners: List[PoolChangeCallback]) -> None:
        for callback in listeners:
            callback(change)

    def _on_connect(self, endpoint: WebsocketEndpoint) -> None:

        add = PoolEvent(Change.add, endpoint, self)
        self._notify_change(add, self.on_before_change)

        def handle_remove(msg: str | bytes | None):
            if msg is None:
                remove = PoolEvent(Change.remove, endpoint, self)
                self._notify_change(remove, self.on_before_change)
                self.clients.remove(endpoint)
                self._notify_change(remove, self.on_after_change)

        endpoint.add_listener(handle_remove)
        self.clients.append(endpoint)
        self._notify_change(add, self.on_after_change)

    def all_clients_rpc(self, rpc_class: Callable[..., T]) -> Iterator[T]:
        for client in self.clients:
            try:
                yield client.rpc(rpc_class)
            except Exception as e:
                logger.error(f'Error during rpc call: {e}')


class ListenerProtocol(Protocol):
    def __call__(self, message: str | bytes | None) -> OptionalCoroutine: ...
    """None means close the connection"""


class SendEndpoint:
    def send(self, message: str | bytes | None) -> OptionalCoroutine: ...
    """None means close the connection"""


class DispatchEndpoint(Protocol):
    def dispatch(self, module: str, func_name: str, *args) -> None: ...


from typing import TypeVar, Callable

T = TypeVar('T')


class WebsocketEndpoint(SendEndpoint):
    listeners: list[ListenerProtocol]

    def add_listener(self, listener: ListenerProtocol) -> None: ...

    # part to be called by user code to send a outgoing message
    def send(self, message: str | bytes | None) -> OptionalCoroutine: ...

    def rpc(self, factory: Callable[..., T]) -> T:
        instance = factory(self)
        return instance


class WebsocketEndpointIO(WebsocketEndpoint):
    def __init__(self, send: ListenerProtocol):
        """The send argument is called by the IO implementation: it will deliver outgoing messages"""
        self._send = send
        self._listener: ListenerProtocol | None = None

    def add_listener(self, listener: ListenerProtocol) -> None:
        if self._listener is not None:
            raise Exception('Only one listener is allowed')
        self._listener = listener

    # part to be called by user code to send a outgoing message
    def send(self, message: str | bytes | None) -> OptionalCoroutine:
        return self._send(message)

    # parte to be used by IO implementation to be called to notify incoming messages
    def on_message(self, message: str | bytes | None) -> OptionalCoroutine:
        if self._listener is not None:
            return self._listener(message)

    def dispatch(self, module: str, func_name: str, *args) -> OptionalCoroutine:
        j = RpcRequest.to_json(module, func_name, *args)
        return self.send(j)
