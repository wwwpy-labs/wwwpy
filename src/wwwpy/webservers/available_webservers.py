from __future__ import annotations
from typing import Iterator, List

from ..webserver import Webserver


class AvailableWebservers:
    def __init__(self) -> None:
        self._classes = _webservers_classes()

    @property
    def ids(self) -> Iterator[str]:
        return map(lambda w: w.__name__, self._classes)

    def new_instance(self) -> Webserver:
        return self._classes[0]()

    def instances(self) -> Iterator[Webserver]:
        for webserver_class in self._classes:
            yield webserver_class()


def _webservers_classes() -> List[type[Webserver]]:
    result: List[type[Webserver]] = []
    try:
        from .tornado import WsTornado
        result.append(WsTornado)
    except:
        pass

    return result


_available_webservers: AvailableWebservers | None = None


def available_webservers() -> AvailableWebservers:
    global _available_webservers
    if _available_webservers is None:
        _available_webservers = AvailableWebservers()
    return _available_webservers
