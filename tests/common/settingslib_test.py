from wwwpy.common.settingslib import Settings


def test_hotreload_self_default(tmp_path):
    target, _ = _new_target(tmp_path)
    assert not target.hotreload_self


def test_hotreload_self_set(tmp_path):
    target, ini = _new_target(tmp_path, '[general]\nhotreload_self=true')

    assert target.hotreload_self


def test_open_url(tmp_path):
    target, _ = _new_target(tmp_path)
    assert not target.open_url_code


def test_open_url_set(tmp_path):
    content = """[general]\nopen_url_code=import os; os.system("open '{url}')"""
    target, ini = _new_target(tmp_path, content)

    assert target.open_url_code == """import os; os.system("open '{url}')"""


def _new_target(tmp_path, content: str = None):
    target = Settings()
    ini = tmp_path / 'foo.ini'
    if content:
        ini.write_text(content)
    target.load(ini)
    return target, ini
