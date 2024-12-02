from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Collection

from wwwpy.bootstrap import bootstrap_routes
from wwwpy.common import quickstart, _remote_module_not_found_console
from wwwpy.common.designer import log_emit
from wwwpy.common.rpc.custom_loader import CustomFinder
from wwwpy.common.settingslib import Settings
from wwwpy.resources import library_resources, from_directory
from wwwpy.rpc import RpcRoute
from wwwpy.server import tcp_port
from wwwpy.server.custom_str import CustomStr
from wwwpy.webserver import Webserver, Route
from wwwpy.webservers.available_webservers import available_webservers
from wwwpy.websocket import WebsocketPool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    directory: Path
    dev_mode: bool
    server_rpc_packages: Collection[str]
    remote_rpc_packages: Collection[str]
    server_folders: Collection[str]
    remote_folders: Collection[str]
    settings: Settings


@dataclass
class Project:
    config: Config
    websocket_pool: WebsocketPool
    routes: tuple[Route]


def start_default(port: int, directory: Path, dev_mode=False, settings: Settings = None):
    webserver = available_webservers().new_instance()

    if quickstart.invalid_project(directory):
        warn_invalid_project(directory)

    convention(directory, webserver, dev_mode=dev_mode, settings=settings)

    while tcp_port.is_port_busy(port):
        logger.warning(f'port {port} is busy, retrying...')
        [time.sleep(0.1) for _ in range(20) if tcp_port.is_port_busy(port)]

    webserver.set_port(port).start_listen()


websocket_pool: WebsocketPool = None


def setup(config: Config) -> Project:
    sys.path.insert(0, CustomStr(config.directory))
    sys.meta_path.insert(0, CustomFinder(set(config.remote_rpc_packages)))

    global websocket_pool
    websocket_pool = WebsocketPool('/wwwpy/ws')

    services = _configure_server_rpc_services('/wwwpy/rpc', list(config.server_rpc_packages))
    services.generate_remote_stubs()

    resources = [
        library_resources(),
        services.remote_stub_resources(),
        from_directory(config.directory / 'remote', relative_to=config.directory),
        from_directory(config.directory / 'common', relative_to=config.directory),
    ]

    routes: list[Route] = [
        services.route,
        websocket_pool.http_route,
        *bootstrap_routes(
            resources=resources,
            python=f'from wwwpy.remote.browser_main import entry_point; await entry_point(dev_mode={config.dev_mode})'
        )
    ]

    if config.dev_mode:
        import wwwpy.server.designer.dev_mode as dev_modelib
        dev_modelib._warning_on_multiple_clients(websocket_pool)

        dev_modelib.start_hotreload(
            config.directory, websocket_pool, services,
            server_folders=set(config.server_folders),
            remote_folders=set(config.remote_folders),
        )
        if config.settings.hotreload_self:
            logger.info('devself detected')
            import wwwpy
            wwwpy_dir = Path(wwwpy.__file__).parent
            wwwpy_package_dir = wwwpy_dir.parent
            dev_modelib.start_hotreload(
                wwwpy_package_dir, websocket_pool, services,
                server_folders={'wwwpy/common', 'wwwpy/server'},
                remote_folders={'wwwpy/common', 'wwwpy/remote'}
            )

    return Project(config, websocket_pool, tuple(routes))


def convention(directory: Path, webserver: Webserver = None, dev_mode=False, settings: Settings = None):
    if settings is None:
        settings = Settings()

    server_rpc_packages = ['server.rpc']
    remote_rpc_packages = {'remote', 'remote.rpc', 'wwwpy.remote', 'wwwpy.remote.rpc'}
    server_folders = {'common', 'server'}
    remote_folders = {'common', 'remote'}

    if dev_mode:
        server_rpc_packages.append('wwwpy.server.designer.rpc')
        remote_rpc_packages.update({'wwwpy.remote.designer', 'wwwpy.remote.designer.rpc'})
        log_emit.add_once(print)

    config = Config(
        directory=directory,
        dev_mode=dev_mode,
        server_rpc_packages=server_rpc_packages,
        remote_rpc_packages=remote_rpc_packages,
        server_folders=server_folders,
        remote_folders=remote_folders,
        settings=settings
    )

    project = setup(config)

    if webserver is not None:
        webserver.set_http_route(*project.routes)


def _configure_server_rpc_services(route_path: str, modules: list[str]) -> RpcRoute:
    services = RpcRoute(route_path)
    for module_name in modules:
        services.allow(module_name)
    return services


def warn_invalid_project(directory: Path):
    content = _remote_module_not_found_console.replace('$[directory]', str(directory.absolute()))
    lines = content.split('\n')
    for line in lines:
        print(line)
    print('Continuing in ', end='', flush=True)
    for text in "3… 2… 1… \n":
        print(text, end='', flush=True)
        time.sleep(0.5)
    print()
