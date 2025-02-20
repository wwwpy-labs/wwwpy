import pytest
from wwwpy.common.designer.packaging import package_manager

package_manager_list = [package_manager.UvPackageManager, package_manager.PipPackageManager]


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages(pm):
    target = pm()
    packages_list = target.installed_packages()
    assert packages_list


@pytest.mark.parametrize("pm", package_manager_list)
def test_installed_packages__should_not_have_wwwpy_twice(pm):
    packages_list = [p for p in pm().installed_packages() if p.name == 'wwwpy']
    assert len(packages_list) == 1
