import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from time import sleep

import pytest
from playwright.sync_api import Page

from tests.server.convention_fixture import start_test_convention
from wwwpy.bootstrap import wrap_in_tryexcept
from wwwpy.common import reloader

logger = logging.getLogger(__name__)


class PageFixture:
    def __init__(self, page: Page, tmp_path: Path, webserver):
        self.page = page
        self.tmp_path = tmp_path
        self.webserver = webserver
        self.remote = self.tmp_path / 'remote'
        self.remote_init = self.remote / '__init__.py'
        self.dev_mode = False

    def set_path(self, path):
        self.tmp_path = path
        self.remote = self.tmp_path / 'remote'
        self.remote_init = self.remote / '__init__.py'

    def evaluate_catch(self, python: str):
        safe_python = wrap_in_tryexcept(python,
                                        'import traceback; from js import console; console.log(f"exception! {traceback.format_exc()}")')
        return self.page.evaluate(f'pyodide.runPythonAsync(`{safe_python}`)')

    def evaluate(self, python: str):
        if '`' in python:
            raise ValueError('` is not allowed in evaluate')
        return self.page.evaluate(f'pyodide.runPythonAsync(`{python}`)')

    def assert_evaluate(self, python: str):
        """Assert on the evaluated python expression. So the evaluated expression should return a Tuple[bool, str]
        This pass through javascript so, beware of using `` separators"""
        __tracebackhide__ = True

        t = self.evaluate(python)
        if isinstance(t, tuple) or isinstance(t, list):
            assert t[0], t[1]
        else:
            assert t

    def assert_evaluate_retry(self, python: str, millis=5000, on_false_eval=None):
        """Assert on the evaluated python expression. So the evaluated expression should return a Tuple[bool, str]
        This pass through javascript so, beware of using `` separators"""
        if '`' in python:
            raise ValueError('` is not allowed in assert_evaluate_retry')
        __tracebackhide__ = True
        from tests.timeouts import timeout_multiplier
        millis = millis * timeout_multiplier()
        delta = timedelta(milliseconds=millis)
        start = datetime.utcnow()
        while True:
            t = self.evaluate(python)
            expr = t[0] if isinstance(t, tuple) or isinstance(t, list) else t
            if expr:
                return
            if on_false_eval:
                on_false_eval()
            sleep(0.2)
            if datetime.utcnow() - start > delta:
                break
            logger.warning(f"retrying assert_evaluate_retry")

        if isinstance(t, tuple) or isinstance(t, list):
            assert t[0], t[1]
        else:
            assert t

    def start_remote(self, remote_init_content: str = None):
        remote_init = self.remote_init
        if remote_init_content:
            remote_init.parent.mkdir(parents=True, exist_ok=True)
            remote_init.write_text(remote_init_content)
        start_test_convention(self.tmp_path, self.webserver, dev_mode=self.dev_mode)
        self.webserver.start_listen()
        self.page.goto(self.webserver.localhost_url())

    def write_module(self, module_path: str, content: str):
        file = self.tmp_path / module_path
        parent = file.parent
        parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)
        init = parent / '__init__.py'
        if not init.exists():
            init.touch()

    def unload(self):
        reloader.unload_path(str(self.tmp_path))


@pytest.fixture
def fixture(page: Page, tmp_path, webserver):
    sys_path = sys.path.copy()
    sys_meta_path = sys.meta_path.copy()
    fix = PageFixture(page, tmp_path, webserver)
    try:
        yield fix
    finally:
        sys.path = sys_path
        sys.meta_path = sys_meta_path
        fix.unload()
