import wwwpy.server.convention
from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.files import get_all_paths_with_hashes


def test_dev_mode_disabled__should_NOT_create_canonical_components(dyn_sys_path: DynSysPath):
    wwwpy.server.convention.convention(dyn_sys_path.path)
    assert get_all_paths_with_hashes(dyn_sys_path.path) == set()


def test_dev_mode_non_empty_folder_but_no_remote__should_not_fail(dyn_sys_path: DynSysPath):
    # dyn_sys_path.path.mkdir('some-folder')
    (dyn_sys_path.path / 'some-folder').mkdir()
    wwwpy.server.convention.convention(dyn_sys_path.path, dev_mode=True)


