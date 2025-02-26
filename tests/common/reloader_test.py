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

def test_simple_import_of_package_module(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('server/__init__.py', '')
    dyn_sys_path.write_module2('server/rpc.py', 'b = 2')

    gl = {}
    lo = {}
    exec('import server.rpc', gl, lo)
    assert lo['server'].rpc.b == 2

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('server/rpc.py', 'b = 42')
    gl = {}
    lo = {}
    exec('import server.rpc', gl, lo)
    assert lo['server'].rpc.b == 42
    assert not hasattr(lo['server'].rpc, 'a')


def test_import_x_as_y(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('server/__init__.py', '')
    dyn_sys_path.write_module2('server/rpc.py', 'b = 2')

    gl = {}
    lo = {}
    exec('import server.rpc as rpc', gl, lo)
    assert lo['rpc'].b == 2

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('server/rpc.py', 'b = 42')

    gl = {}
    lo = {}
    exec('import server.rpc as rpc', gl, lo)
    assert lo['rpc'].b == 42
    assert not hasattr(lo['rpc'], 'a')

def test_from_x_import_y(dyn_sys_path: DynSysPath):
    # GIVEN
    dyn_sys_path.write_module2('server/__init__.py', '')
    dyn_sys_path.write_module2('server/rpc.py', 'b = 2')
    from server import rpc  # noqa
    assert rpc.b == 2

    # WHEN
    unload_path(str(dyn_sys_path.path))

    # THEN
    dyn_sys_path.write_module2('server/rpc.py', 'b = 42')
    from server import rpc  # noqa
    assert rpc.b == 42
    assert not hasattr(rpc, 'a')
