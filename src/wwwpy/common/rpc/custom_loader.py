import importlib
import importlib.abc
import importlib.util
import sys
import ast
from typing import Set

from wwwpy.common.rpc import func_registry
from ast import Module, FunctionDef, AsyncFunctionDef, ClassDef


class CustomLoader(importlib.abc.Loader):
    def __init__(self, loader):
        self.loader = loader

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        module_name = module.__name__
        source = self.loader.get_source(module_name)
        proxy_source = func_registry.source_to_proxy(module_name, source)
        code = compile(proxy_source, module.__file__, 'exec')
        exec(code, module.__dict__)


class CustomFinder(importlib.abc.MetaPathFinder):
    """It intercepts the packages specified and rewrites them as a proxy-to-remote.
    The goal is to seamlessly invoke remote functions from the server"""

    def __init__(self, packages_name: Set[str], custom_loader=CustomLoader):
        self.custom_loader = custom_loader
        self.packages_name = packages_name
        super().__init__()

    def find_spec(self, fullname, path, target=None):
        if fullname in self.packages_name:
            # Temporarily remove this finder from sys.meta_path to avoid recursion. Remove also pytest rewriter hook
            orig = sys.meta_path.copy()
            sys.meta_path = [f for f in sys.meta_path if not isinstance(f, CustomFinder)]
            sys.meta_path = [f for f in sys.meta_path if f.__class__.__name__ != 'AssertionRewritingHook']
            try:
                spec = importlib.util.find_spec(fullname)
            finally:
                # Reinsert this finder back into sys.meta_path
                sys.meta_path = orig

            if spec:
                spec.loader = self.custom_loader(spec.loader)
            return spec
        return None
