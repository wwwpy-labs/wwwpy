from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Collection, Sequence

from wwwpy.bootstrap import bootstrap_routes
from wwwpy.common import loglib
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
    """
    It may be that we need to split this in the following logic blocks:
    - dev_mode flag
    - (a set of) 'directory' has it's common/remote/server set of folders
        - this will impact the hot reload mechanism and the bundle to be sent to the remote
    - keep 'common' separate from 'remote' and 'server' folders ?
    - todo continue this analysis
    """
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
    routes: Sequence[Route]


def setup(config: Config, settings: Settings = None) -> Project:
    """This function is used / should be used from these points:
    - wwwpy main module
    - remote tests, i.e., XVirtImpl to setup the infrastructure to run tests
    - server tests, i.e. those using Playwright
    """
    if settings is None:
        settings = Settings()

    loglib.set_log_level(settings.log_level)
    
    directory = config.directory
    sys.path.insert(0, CustomStr(directory))
    sys.meta_path.insert(0, CustomFinder(set(config.remote_rpc_packages)))

    websocket_pool = WebsocketPool('/wwwpy/ws')

    services = _configure_server_rpc_services('/wwwpy/rpc', list(config.server_rpc_packages))
    services.generate_remote_stubs()

    resources = [library_resources(), services.remote_stub_resources(), ] + \
                [from_directory(directory / f, relative_to=directory) for f in config.remote_folders]

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
            directory, websocket_pool, services,
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
