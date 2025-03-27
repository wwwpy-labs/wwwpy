import logging
import warnings
from typing import Callable


class _CustomHandler(logging.Handler):
    def __init__(self, callback: Callable[[str], None]):
        super().__init__()
        self._emit = callback

    def emit(self, record: logging.LogRecord):
        log_entry = self.format(record)
        self._emit(log_entry)


def add_once(emit: Callable[[str], None]):
    logging.getLogger('tornado.access').setLevel(logging.ERROR)

    for log_name in ['common', 'remote', 'server']:
        logging.getLogger(log_name).setLevel(logging.DEBUG)

    root = logging.getLogger()

    for handler in root.handlers:
        if isinstance(handler, _CustomHandler):
            return
    from wwwpy.common.detect import is_pyodide
    # side = 'R' if is_pyodide() else 'S'
    side = '🌎' if is_pyodide() else '🏛'
    formatter = logging.Formatter(f'%(asctime)s {side} %(levelname).1s %(name)s:%(lineno)d - %(message)s')
    custom_handler = _CustomHandler(emit)
    custom_handler.setFormatter(formatter)
    root.addHandler(custom_handler)


_original_showwarning = None


def _custom_showwarning(message, category, filename, lineno, file=None, line=None):
    if _original_showwarning:
        _original_showwarning(message, category, filename, lineno, file, line)
    log_entry = f'{category.__name__}: {message} ({filename}:{lineno})'
    logging.getLogger('common').warning(log_entry)


def warning_to_log():
    global _original_showwarning
    if _original_showwarning:
        return
    _original_showwarning = warnings.showwarning
    warnings.showwarning = _custom_showwarning
