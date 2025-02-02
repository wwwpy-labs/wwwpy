from __future__ import annotations

import time
from pathlib import Path

from wwwpy.common import quickstart
from wwwpy.common.designer import log_emit
from wwwpy.server import tcp_port
from wwwpy.server.configure import Project, logger, Config, setup
from wwwpy.server.settingslib import user_settings
from wwwpy.webservers.available_webservers import available_webservers

_projects: list[Project] = []


def default_project() -> Project:
    if len(_projects) == 0:
        raise ValueError('The default project has not been set')
    return _projects[0]


def add_project(project: Project):
    _projects.append(project)


def start_default(directory: Path, port: int, dev_mode=False) -> Project:
    quickstart.warn_if_unlikely_project(directory)

    config = default_config(directory, dev_mode)
    project = setup(config, user_settings())
    add_project(project)

    webserver = available_webservers().new_instance()
    webserver.set_routes(*project.routes)

    while tcp_port.is_port_busy(port):
        logger.warning(f'port {port} is busy, retrying...')
        [time.sleep(0.1) for _ in range(20) if tcp_port.is_port_busy(port)]

    webserver.set_port(port).start_listen()

    return project


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
