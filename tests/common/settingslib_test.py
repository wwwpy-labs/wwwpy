from pathlib import Path

import pytest

from wwwpy.common.settingslib import Settings


class Fix:
    def __init__(self, tmp_path: Path):
        self.target = Settings()
        self.ini = tmp_path / 'foo.ini'
        self.tmp_path = tmp_path

    def write_load(self, content):
        self.ini.write_text(content)
        self.target.load(self.ini)


@pytest.fixture
def fix(tmp_path) -> Fix:
    return Fix(tmp_path)


def test_hotreload_self_default(fix: Fix):
    assert not fix.target.hotreload_self


def test_hotreload_self_set(fix: Fix):
    fix.write_load('[general]\nhotreload_self=true')
    assert fix.target.hotreload_self


def test_open_url(fix: Fix):
    assert not fix.target.open_url_code


def test_open_url_set(fix: Fix):
    fix.write_load("""[general]\nopen_url_code=import os; os.system("open '{url}')""")
    assert fix.target.open_url_code == """import os; os.system("open '{url}')"""


def test_log_level_empty(fix: Fix):
    assert {} == fix.target.log_level


def test_log_level(fix: Fix):
    fix.write_load("""[log_level]\nmod1.mod2=DEBUG\nmod3=INFO""")
    assert {'mod1.mod2': 'DEBUG', 'mod3': 'INFO'} == fix.target.log_level


def _new_target(tmp_path, content: str = None):
    target = Settings()
    ini = tmp_path / 'foo.ini'
    if content:
        ini.write_text(content)
    target.load(ini)
    return target, ini
