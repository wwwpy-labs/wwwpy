from __future__ import annotations

import inspect
import logging
import sys

logger = logging.getLogger(__name__)

def reload(module):
    import importlib
    # importlib.invalidate_caches()
    return importlib.reload(module)


def unload_path(path: str, skip_wwwpy: bool = False):
    def accept(module):
        try:
            module_path = inspect.getfile(module)
            return module_path.startswith(path) and module_path != __file__
        except:
            return False

    names = [name for name, module in sys.modules.items() if accept(module)]

    for name in names:
        if skip_wwwpy and name.startswith('wwwpy.') or name == 'wwwpy':
            logger.debug(f'hot-reload: skip module `{name}`')
        else:
            logger.debug(f'hot-reload: unload module `{name}`')
            del (sys.modules[name])
