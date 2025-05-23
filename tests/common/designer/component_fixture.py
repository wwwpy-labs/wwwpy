from pathlib import Path

import pytest

from tests.common import DynSysPath, dyn_sys_path


# todo should be merged/refactored with TargetFixture
class ComponentFixture:
    def __init__(self, dyn_sys_path: DynSysPath):
        self._source = None
        self.dyn_sys_path: DynSysPath = dyn_sys_path

    def write_component(self, path: str, class_name: str, html: str = '') -> Path:
        return self.dyn_sys_path.write_module2(path, f'''
class {class_name}:
    def init_component(self):
        self.element.innerHTML = """{html}"""
''')


@pytest.fixture
def component_fixture(dyn_sys_path: DynSysPath):
    return ComponentFixture(dyn_sys_path)
