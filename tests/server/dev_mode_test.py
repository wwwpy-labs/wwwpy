import logging
from datetime import timedelta, datetime
from time import sleep

from playwright.sync_api import expect

from tests import for_all_webservers
from tests.server.page_fixture import PageFixture, fixture
from tests.timeouts import timeout_multiplier
from wwwpy.common import quickstart
from wwwpy.common.files import get_all_paths_with_hashes
from wwwpy.common.quickstart import is_empty_project
from wwwpy.common.tree import print_tree

logger = logging.getLogger(__name__)


@for_all_webservers()
def test_dev_mode_with_empty_project__should_show_quickstart_dialog(fixture: PageFixture):
    logger.info('test_dev_mode_with_empty_project__should_show_quickstart_dialog -- marker to separate logs')
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

    logger.debug('accepting quickstart')
    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
not DevModeComponent.instance.quickstart.accept_quickstart('basic')
""")

    logger.debug('checking quickstart applied')
    # language=python
    fixture.assert_evaluate_retry("""
from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
DevModeComponent.instance.quickstart.window.element.isConnected is False
""")

    def print_server_fs():
        print_tree(fixture.tmp_path / 'remote')

    logger.debug(f'Going to verify if component-1 is attached with a specific 42000ms timeout')
    try:
        # expect(fixture.page.locator('component-1')).to_be_attached(timeout=42000)
        # language=python
        fixture.assert_evaluate_retry("""
import js
'<component-1>' in js.document.body.innerHTML , f'html=[[[{js.document.body.innerHTML}]]]'
""", on_false_eval=print_server_fs)
    except Exception as e:
        logger.error(f"Assertion failed: component-1 not attached. Error: {e}")
        body_html = fixture.page.evaluate("() => document.body.innerHTML")
        logger.debug(f"Body HTML content:\n`{body_html}`")
        # language=python
        fixture.evaluate("""
from wwwpy.common.tree import print_tree
print_tree('/wwwpy_bundle/remote')
        """)
        print_server_fs()
        raise

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
