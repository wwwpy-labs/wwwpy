from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Collection

from wwwpy.bootstrap import bootstrap_routes
from wwwpy.common import _remote_module_not_found_console
from wwwpy.common.designer import log_emit
from wwwpy.common.rpc.custom_loader import CustomFinder
from wwwpy.common.settingslib import Settings
from wwwpy.resources import library_resources, from_directory
from wwwpy.rpc import RpcRoute
from wwwpy.server.custom_str import CustomStr
from wwwpy.webserver import Route
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


@dataclass
class Project:
    config: Config
    settings: Settings
    websocket_pool: WebsocketPool
    routes: tuple[Route]


def default_config(directory: Path, dev_mode: bool) -> Config:
    server_rpc_packages = ['server.rpc']
    remote_rpc_packages = {'remote', 'remote.rpc', 'wwwpy.remote', 'wwwpy.remote.rpc'}
    server_folders = {'common', 'server'}
    remote_folders = {'common', 'remote'}

    if dev_mode:
        server_rpc_packages.append('wwwpy.server.designer.rpc')
        remote_rpc_packages.update({'wwwpy.remote.designer', 'wwwpy.remote.designer.rpc'})
        log_emit.add_once(print)

    return Config(
        directory=directory,
        dev_mode=dev_mode,
        server_rpc_packages=server_rpc_packages,
        remote_rpc_packages=remote_rpc_packages,
        server_folders=server_folders,
        remote_folders=remote_folders
    )


def setup(config: Config, settings: Settings = None) -> Project:
    if settings is None:
        settings = Settings()

    sys.path.insert(0, CustomStr(config.directory))
    sys.meta_path.insert(0, CustomFinder(set(config.remote_rpc_packages)))

    websocket_pool = WebsocketPool('/wwwpy/ws')

    services = _configure_server_rpc_services('/wwwpy/rpc', list(config.server_rpc_packages))
    services.generate_remote_stubs()

    resources = [
        library_resources(),
        services.remote_stub_resources(),
        # todo 'remote' and 'common' should be taken from the config.remote_folders
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
        if settings.hotreload_self:
            logger.info('devself detected')
            import wwwpy
            wwwpy_dir = Path(wwwpy.__file__).parent
            wwwpy_package_dir = wwwpy_dir.parent
            dev_modelib.start_hotreload(
                wwwpy_package_dir, websocket_pool, services,
                server_folders={'wwwpy/common', 'wwwpy/server'},
                remote_folders={'wwwpy/common', 'wwwpy/remote'}
            )

    return Project(config, settings, websocket_pool, tuple(routes))


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
