from datetime import timedelta, datetime
from time import sleep

from playwright.sync_api import expect

from tests import for_all_webservers
from tests.timeouts import timeout_multiplier
from tests.server.page_fixture import PageFixture, fixture
from wwwpy.common import quickstart
from wwwpy.common.files import get_all_paths_with_hashes
from wwwpy.common.quickstart import is_empty_project

import logging

logger = logging.getLogger(__name__)


@for_all_webservers()
def test_dev_mode_with_empty_project__should_show_quickstart_dialog(fixture: PageFixture):
    fixture.dev_mode = True
    assert list(fixture.tmp_path.iterdir()) == []
    fixture.start_remote()
    assert is_empty_project(fixture.tmp_path)

    expect(fixture.page.locator('wwwpy-dev-mode-component')).to_be_attached()

    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
DevModeComponent.instance.quickstart is not None
""")
    assert is_empty_project(fixture.tmp_path)

    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
not DevModeComponent.instance.toolbox.visible
""")

    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
not DevModeComponent.instance.quickstart.accept_quickstart('basic')
""")

    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
DevModeComponent.instance.quickstart.window.element.isConnected is False
""")

    expect(fixture.page.locator('component-1')).to_be_attached()

    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
DevModeComponent.instance.toolbox.visible
""")
    return
    def project_is_right():
        if is_empty_project(fixture.tmp_path):
            return False, 'project is empty'
        dir1 = quickstart.quickstart_list().get('basic').path
        dir2 = fixture.tmp_path
        dir1_set = get_all_paths_with_hashes(dir1)
        dir2_set = get_all_paths_with_hashes(dir2)
        return dir1_set in dir2_set, f'{dir1_set} != {dir2_set}\n\n{dir1}\n\n{dir2}'

    _assert_retry_millis(project_is_right)


def _assert_retry_millis(condition, millis=5000):
    __tracebackhide__ = True
    millis = millis * timeout_multiplier()
    delta = timedelta(milliseconds=millis)
    start = datetime.utcnow()
    while True:
        t = condition()
        expr = t[0] if isinstance(t, tuple) or isinstance(t, list) else t
        if expr:
            return
        sleep(0.2)
        if datetime.utcnow() - start > delta:
            break
        logger.warning(f"retrying assert_evaluate_retry")

    if isinstance(t, tuple) or isinstance(t, list):
        assert t[0], t[1]
    else:
        assert t
