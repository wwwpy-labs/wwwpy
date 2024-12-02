from __future__ import annotations

from wwwpy.server.configure import Project

_projects: list[Project] = []


def default_project() -> Project:
    if len(_projects) == 0:
        raise ValueError('The default project has not been set')
    return _projects[0]


def add_project(project: Project):
    _projects.append(project)
