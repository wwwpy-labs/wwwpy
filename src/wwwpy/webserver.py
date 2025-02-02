from __future__ import annotations

from abc import ABC, abstractmethod
from time import sleep
from typing import Union

from wwwpy.http import HttpRoute
from wwwpy.server.wait_url import wait_url
from wwwpy.websocket import WebsocketRoute

Route = Union[HttpRoute, WebsocketRoute]


class Webserver(ABC):
    def __init__(self) -> None:
        self.host: str = '0.0.0.0'
        self.port: int = 7777

    def set_host(self, host: str) -> 'Webserver':
        self.host = host
        return self

    def set_port(self, port: int) -> 'Webserver':
        self.port = port
        return self

    def start_listen(self) -> 'Webserver':
        indent = '    '
        device_ip = f'{indent}http://{_get_ip()}:{self.port}\n' if self.host == '0.0.0.0' else ''
        print(f'Available at (non-exhaustive list):\n' +
              device_ip +
              f'{indent}{self.localhost_url()}\n'
              )
        self._start_listen()
        self.wait_ready()
        return self

    def set_routes(self, *routes: Route) -> 'Webserver':
        for route in routes:
            self._setup_route(route)
        return self

    @abstractmethod
    def _setup_route(self, route: Route) -> None:
        pass

    @abstractmethod
    def _start_listen(self) -> None:
        pass

    def wait_ready(self) -> 'Webserver':
        wait_url(self.localhost_url() + '/check_if_webserver_is_accepting_requests')
        return self

    def localhost_url(self) -> str:
        return f'http://127.0.0.1:{self.port}'


def wait_forever() -> None:
    while True:
        sleep(10)


def _get_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
