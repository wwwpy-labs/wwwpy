from __future__ import annotations

import inspect
import sys

import logging

logger = logging.getLogger(__name__)

def reload(module):
    import importlib
    # importlib.invalidate_caches()
    return importlib.reload(module)


def unload_path(path: str):
    def accept(module):
        try:
            module_path = inspect.getfile(module)
            return module_path.startswith(path) and module_path != __file__
        except:
            return False

    names = [name for name, module in sys.modules.items() if accept(module)]

    for name in names:
        logger.debug(f'hot-reload: unload module {name}...')
        del (sys.modules[name])
