import logging
from functools import partial
from typing import Iterable

import pytest

from wwwpy.server.tcp_port import find_port
from wwwpy.webserver import Webserver
from wwwpy.webservers.available_webservers import available_webservers

logger = logging.getLogger(__name__)


def _webservers_instances() -> Iterable[Webserver]:
    for i in available_webservers().instances():
        i.set_port(find_port())
        yield i


def for_all_webservers():
    return partial(pytest.mark.parametrize, 'webserver', _webservers_instances(),
                   ids=available_webservers().ids)()

