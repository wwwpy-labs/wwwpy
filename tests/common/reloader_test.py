from tests.common import DynSysPath, dyn_sys_path
from wwwpy.common.reloader import unload_path


def test_simple_reload__of_import(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('p1/__init__.py', 'a = 1')
    import p1
    assert p1.a == 1

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('p1/__init__.py', 'b = 123')
    import p1
    assert p1.b == 123
    assert not hasattr(p1, 'a')


def test_simple_reload__of_module_import(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('p1.py', 'a = 1')
    import p1
    assert p1.a == 1

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('p1.py', 'b = 123')
    import p1
    assert p1.b == 123
    assert not hasattr(p1, 'a')


def test_simple_reload__of_exec(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('p1/__init__.py', 'a = 1')
    gl = {}
    lo = {}
    exec('import p1', gl, lo)
    assert lo['p1'].a == 1

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('p1/__init__.py', 'b = 123')
    gl = {}
    lo = {}
    exec('import p1', gl, lo)
    assert lo['p1'].b == 123
    assert not hasattr(lo['p1'], 'a')
