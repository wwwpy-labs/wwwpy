from __future__ import annotations

import time
from pathlib import Path

from wwwpy.common import quickstart
from wwwpy.server import tcp_port

from wwwpy.server.configure import Project, warn_invalid_project, logger, default_config, setup
from wwwpy.server.settingslib import user_settings
from wwwpy.webserver import Webserver
from wwwpy.webservers.available_webservers import available_webservers

_projects: list[Project] = []


def default_project() -> Project:
    if len(_projects) == 0:
        raise ValueError('The default project has not been set')
    return _projects[0]


def add_project(project: Project):
    _projects.append(project)


def start_default(port: int, directory: Path, dev_mode=False) -> Project:
    webserver = available_webservers().new_instance()

    if quickstart.invalid_project(directory):
        warn_invalid_project(directory)

    project = convention(directory, webserver, dev_mode=dev_mode)

    while tcp_port.is_port_busy(port):
        logger.warning(f'port {port} is busy, retrying...')
        [time.sleep(0.1) for _ in range(20) if tcp_port.is_port_busy(port)]

    webserver.set_port(port).start_listen()

    return project


def convention(directory: Path, webserver: Webserver = None, dev_mode=False) -> Project:
    config = default_config(directory, dev_mode)
    project = setup(config, user_settings())
    add_project(project)
    if webserver is not None:
        webserver.set_http_route(*project.routes)

    return project
