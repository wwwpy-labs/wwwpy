import importlib
import sys

from tests.common import dyn_sys_path, DynSysPath
from wwwpy.common.rpc.custom_loader import CustomFinder


def test_remote_rpc_interceptor(dyn_sys_path: DynSysPath):
    """Importing remote.rpc should not raise an exception even from the server side
    even though it imports 'js' that does not exist on the server side.
    It is because the import process of such package is handled and modified"""
    factory = MockLoaderFactory()
    target = CustomFinder({'remote.rpc'}, factory.MockLoader)
    sys.meta_path.insert(0, target)
    dyn_sys_path.write_module2('remote/rpc.py', ' not even python code')
    import remote
    assert remote

    import remote.rpc
    assert remote.rpc

    assert len(factory.mock_loaders) == 1
    assert factory.mock_loaders[0].sources == [' not even python code']


class MockLoaderFactory:
    def __init__(self):
        self.mock_loaders = []
        parent = self

        class MockLoader(importlib.abc.Loader):
            def __init__(self, loader):
                self.loader = loader
                self.sources = []
                parent.mock_loaders.append(self)

            def create_module(self, spec):
                return None

            def exec_module(self, module):
                module_name = module.__name__
                source = self.loader.get_source(module_name)
                self.sources.append(source)

        self.MockLoader = MockLoader
