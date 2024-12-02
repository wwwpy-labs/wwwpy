from __future__ import annotations

from pathlib import Path

from wwwpy.common.settingslib import Settings
from wwwpy.server.configure import Project, setup
from wwwpy.server.convention import default_config, add_project
from wwwpy.webserver import Webserver


def start_test_convention(directory: Path, webserver: Webserver = None, dev_mode=False) -> Project:
    config = default_config(directory, dev_mode)
    project = setup(config, Settings())

    if webserver is not None:
        webserver.set_http_route(*project.routes)

    return project
