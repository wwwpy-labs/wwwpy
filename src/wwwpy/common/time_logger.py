from __future__ import annotations

import logging
import time
from datetime import timedelta

logger = logging.getLogger(__name__)


class TimeLogger:
    def __init__(self, name):
        self.name = name
        self.start = time.perf_counter()

    def debug(self, message=''):
        logger.debug(self.message(message), stacklevel=2)

    def message(self, msg='') -> str:
        delta = self.time_spent()
        if msg:
            msg = f' - {msg}'
        return f'{self.name}{msg} time={delta}'

    def time_spent(self) -> timedelta:
        end = time.perf_counter()
        return timedelta(seconds=end - self.start)
