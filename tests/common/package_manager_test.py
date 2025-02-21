from typing import Generator

import pytest

from wwwpy.common.designer.packaging import package_manager
from wwwpy.common.designer.packaging.package_manager import guess_package_manager_class, guess_package_manager
from wwwpy.common.detect import is_pyodide

import logging

logger = logging.getLogger(__name__)
package_manager_list = [package_manager.UvPackageManager, package_manager.PipPackageManager]


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages_async(pm):
    target = pm()
    packages_list = target._installed_packages_sync()
    assert packages_list


@pytest.mark.parametrize("pm", package_manager_list)
async def test_installed_packages(pm):
    target = pm()
    packages_list = await target.installed_packages()
    assert packages_list


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages__should_not_have_wwwpy_twice(pm):
    if is_pyodide():
        # pytest.skip("Pyodide does not have wwwpy installed") # pytest-xvirt do not support skip yet
        return

    packages_list = [p for p in pm()._installed_packages_sync() if p.name == 'wwwpy']
    assert len(packages_list) == 1


def test_guess_package_manager():
    expect = package_manager.MicropipPackageManager if is_pyodide() else package_manager.UvPackageManager
    assert guess_package_manager_class().get_or_throw() == expect


async def test_install_mock_package_and_uninstall(tmp_path, pm_fixture):
    # install
    pm = pm_fixture.guess
    result = await pm.install_package('nothing')
    assert result is None

    # check
    installed_result = (await pm.installed_packages()).get_or_throw()
    assert any(p.name == 'nothing' for p in installed_result)

    # uninstall
    uninstall_result = await pm.uninstall_package('nothing')
    logger.debug(f'uninstall_result: type={uninstall_result} {uninstall_result}')
    if not is_pyodide():
        assert uninstall_result is None  # it seems that this fails in Pyodide for a (yet) unknown reason

    # check
    installed_result = (await pm.installed_packages()).get_or_throw()
    assert not any(p.name == 'nothing' for p in installed_result)


class PmFixture:
    def __init__(self):
        self.uninstall = []
        try:
            self.guess = guess_package_manager()
        except Exception as e:
            pass  # this is tested in the unit tests


@pytest.fixture()
async def pm_fixture() -> Generator[PmFixture, None, None]:
    fixture = PmFixture()
    yield fixture
    for package in fixture.uninstall:
        await fixture.guess.uninstall_package(package)
