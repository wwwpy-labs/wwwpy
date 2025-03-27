from __future__ import annotations

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
            module_file = getattr(module, '__file__', None)
            if module_file:
                return module_file.startswith(path) and module_file != __file__
            module_path = getattr(module, '__path__', None)
            if module_path:
                acc = any(p.startswith(path) for p in module_path)
                if acc and not all(p.startswith(path) for p in module_path):
                    logger.warning(f'hot-reload: module `{module}` has mixed paths: {module_path}')
                return acc
        except:
            return False

    names = [name for name, module in sys.modules.items() if accept(module)]

    for name in names:
        if skip_wwwpy and name.startswith('wwwpy.') or name == 'wwwpy':
            logger.debug(f'hot-reload: skip module `{name}`')
        else:
            logger.debug(f'hot-reload: unload module `{name}`')
            del (sys.modules[name])
