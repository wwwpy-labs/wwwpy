import wwwpy.server.conv
from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common import modlib
from wwwpy.common.files import get_all_paths_with_hashes
from wwwpy.server import configure


def test_dev_mode_disabled__should_NOT_create_canonical_components(dyn_sys_path: DynSysPath):
    wwwpy.server.conv.convention(dyn_sys_path.path)
    assert get_all_paths_with_hashes(dyn_sys_path.path) == set()


def test_dev_mode_non_empty_folder_but_no_remote__should_not_fail(dyn_sys_path: DynSysPath):
    # dyn_sys_path.path.mkdir('some-folder')
    (dyn_sys_path.path / 'some-folder').mkdir()
    wwwpy.server.conv.convention(dyn_sys_path.path, dev_mode=True)


