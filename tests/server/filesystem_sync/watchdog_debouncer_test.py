from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import List

from tests.timeouts import timeout_multiplier
from wwwpy.common.filesystem.sync import Event
from wwwpy.server.filesystem_sync.watchdog_debouncer import WatchdogDebouncer


def test_basic_event_expectation(tmp_path: Path):
    """Testing on multiplatform watchdog events and behavior is very difficult. Let's keep it simple"""
    # GIVEN
    events = []

    def callback(evs: List[Event]):
        events.extend(evs)

    target = WatchdogDebouncer(tmp_path, timedelta(milliseconds=200 * timeout_multiplier()), callback)
    target.start()
    file_path = tmp_path / 'test_file.txt'
    file_path.touch()

    # WHEN

    # wait debouncing
    _wait_condition(lambda: target.debouncer.is_debouncing)
    _wait_condition(lambda: not target.debouncer.is_debouncing)

    # THEN

    assert events != [], f'events={events}'


def _wait_condition(condition):
    __tracebackhide__ = True
    [sleep(0.1) for _ in range(5 * timeout_multiplier()) if not condition()]
    assert condition(), 'wait_condition timeout'
