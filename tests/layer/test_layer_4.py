from pathlib import Path

from playwright.sync_api import Page, expect

from tests import for_all_webservers
from tests.common import restore_sys_path
from wwwpy.resources import from_directory
from wwwpy.server import configure
from wwwpy.webserver import Webserver

file_parent = Path(__file__).parent


@for_all_webservers()
def test_server_convention_b(page: Page, webserver: Webserver, restore_sys_path):
    _test_convention('convention_b', page, webserver)


@for_all_webservers()
def test_server_convention_c_async(page: Page, webserver: Webserver, restore_sys_path):
    _test_convention('convention_c_async', page, webserver)


@for_all_webservers()
def test_server_convention_c_sync(page: Page, webserver: Webserver, restore_sys_path):
    _test_convention('convention_c_sync', page, webserver)


@for_all_webservers()
def test_server_convention_empty__folder(page: Page, webserver: Webserver, restore_sys_path, tmp_path: Path):
    configure.convention(tmp_path, webserver)
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    from wwwpy.common import _no_remote_infrastructure_found_text
    expect(page.locator("body")).to_contain_text(_no_remote_infrastructure_found_text)


@for_all_webservers()
def test_empty__folder__error_message(page: Page, webserver: Webserver, restore_sys_path, tmp_path: Path):
    configure.convention(tmp_path, webserver)
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    from wwwpy.common import _no_remote_infrastructure_found_text
    expect(page.locator("body")).to_contain_text(_no_remote_infrastructure_found_text)


def _test_convention(directory, page, webserver):
    configure.convention(file_parent / 'layer_4_support' / directory, webserver)
    webserver.start_listen()
    page.goto(webserver.localhost_url())
    expect(page.locator('id=tag1')).to_have_value(directory)
