from __future__ import annotations

import json
import threading
from functools import partial
from pathlib import Path
from queue import Queue
from time import sleep
from typing import Tuple

from xvirt import XVirt

from wwwpy.bootstrap import bootstrap_routes
from wwwpy.common import modlib
from wwwpy.http import HttpRoute, HttpRequest, HttpResponse
from wwwpy.resources import library_resources, StringResource, from_directory_lazy
from wwwpy.server.tcp_port import find_port
from wwwpy.webservers.available_webservers import available_webservers
from .playwrightlib import start_playwright_in_thread, PlaywrightArgs
from ..configure import _configure_server_rpc_services

_file_parent = Path(__file__).parent

xvirt_instances: list[XVirtImpl] = []


class XVirtImpl(XVirt):

    def __init__(self, headless: bool = True):
        self.headless = headless

        self.events = Queue()
        self.close_pw = threading.Event()
        self.playwright_args: PlaywrightArgs = None
        xvirt_instances.append(self)

    def virtual_path(self) -> str:
        location = modlib._find_module_path('tests.remote')
        if not location:
            return 'tests.remote-not-available'
        return str(location.parent)

    def _http_handler(self, req: HttpRequest, res) -> None:
        # print(f'server side xvirt_notify_handler({req})')
        self.events.put(req.content)
        # return HttpResponse('', 'text/plain')
        res(HttpResponse('', 'text/plain'))

    def run(self):
        webserver = self._start_webserver()
        self.playwright_args = start_playwright_in_thread(webserver.localhost_url(), self.headless)

    def _start_webserver(self):
        # todo refactor and unify this with convention.py, default_config(), setup()
        xvirt_notify_route = HttpRoute('/xvirt_notify', self._http_handler)
        remote_conftest = (_file_parent / 'remote_conftest.py').read_text() \
            .replace('#xvirt_notify_path_marker#', '/xvirt_notify')

        def fs_iterable(package_name: str) -> Tuple[Path | None, Path | None]:
            target = modlib._find_package_directory(package_name)
            if not target:
                return None, None
            root = target.parent
            r = range(package_name.count('.'))
            for _ in r:
                root = root.parent

            return target, root

        services = _configure_server_rpc_services('/wwwpy/rpc', ['wwwpy.server.rpc4tests'])
        services.generate_remote_stubs()

        resources = [library_resources(),
                     from_directory_lazy(partial(fs_iterable, 'remote')),
                     from_directory_lazy(partial(fs_iterable, 'common')),
                     from_directory_lazy(partial(fs_iterable, 'tests.remote')),
                     from_directory_lazy(partial(fs_iterable, 'tests.common')),
                     services.remote_stub_resources(),
                     [
                         StringResource('tests/__init__.py', ''),
                         StringResource('pytest.ini', ''),
                         StringResource('conftest.py', remote_conftest),
                         StringResource('remote_test_main.py',
                                        (_file_parent / 'remote_test_main.py').read_text())],

                     ]
        webserver = available_webservers().new_instance()
        invocation_dir, args = self.remote_invocation_params('/wwwpy_bundle')
        invocation_dir_json = json.dumps(invocation_dir)
        args_json = json.dumps(args)
        rootpath = json.dumps('/wwwpy_bundle')
        bootstrap_python = f'import remote_test_main; await remote_test_main.main({rootpath},{invocation_dir_json},{args_json})'
        webserver.set_routes(*bootstrap_routes(resources, python=bootstrap_python, jspi=True),
                             xvirt_notify_route, services.route)
        webserver.set_port(find_port()).start_listen()
        return webserver

    def finalize(self):
        if not self.headless:
            while True: sleep(1)
        self.close_pw.set()
        self.playwright_args.queue.put(None)
        # self._thread.join()

    def recv_event(self) -> str:
        return self.events.get(timeout=30)
