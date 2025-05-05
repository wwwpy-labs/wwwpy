# wwwpy/pytest_plugin.py

import pytest

from .playwrightlib import playwright_setup_page_logger
from .xvirt_impl import XVirtImpl


def pytest_addoption(parser):
    parser.addoption("--headful", action="store_true", default=False, help="run tests in headfull mode")


def pytest_configure(config):
    # This function is called before any tests or fixtures are collected.
    # You can add any setup code here.

    # For example, you can add your conftest.py setup code here.
    # Note: You might need to adjust this code to work in this context.
    from .playwrightlib import playwright_patch_timeout
    playwright_patch_timeout()


@pytest.hookimpl
def pytest_xvirt_setup(config):
    import wwwpy.base_conf
    headful = config.getoption("--headful") or wwwpy.base_conf.PLAYWRIGHT_HEADFUL
    return XVirtImpl(headless=not headful)


def pytest_unconfigure(config):
    # This function is called after all tests and fixtures have been collected.
    # You can add any teardown code here.
    pass


@pytest.fixture(autouse=True)
def before_each_after_each(request):
    if 'page' not in request.node.fixturenames:
        yield
        return
    page = request.getfixturevalue('page')
    playwright_setup_page_logger(page)
    yield
