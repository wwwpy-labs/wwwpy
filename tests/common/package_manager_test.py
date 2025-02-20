import pytest
from wwwpy.common.designer.packaging import package_manager
from wwwpy.common.designer.packaging.package_manager import guess_package_manager
from wwwpy.common.detect import is_pyodide

package_manager_list = [package_manager.UvPackageManager, package_manager.PipPackageManager]


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages(pm):
    target = pm()
    packages_list = target.installed_packages()
    assert packages_list


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages__should_not_have_wwwpy_twice(pm):
    if is_pyodide():
        # pytest.skip("Pyodide does not have wwwpy installed") # pytest-xvirt do not support skip yet
        return

    packages_list = [p for p in pm().installed_packages() if p.name == 'wwwpy']
    assert len(packages_list) == 1


def test_guess_package_manager():
    expect = package_manager.MicropipPackageManager if is_pyodide() else package_manager.UvPackageManager
    assert guess_package_manager().get_or_throw() == expect
