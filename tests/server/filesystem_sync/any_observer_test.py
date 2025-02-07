from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import List

import pytest
from watchdog.events import FileSystemEvent

from tests.timeouts import timeout_multiplier
from wwwpy.server.filesystem_sync.any_observer import AnyObserver
from wwwpy.server.filesystem_sync import any_observer

any_observer.logger.setLevel('DEBUG')


class Fixture:
    def __init__(self, path: Path):
        self.path = path
        self.events = []
        self.target = AnyObserver(self.path, self._callback)

    def _callback(self, event: FileSystemEvent):
        self.events.append(event)

    def assert_has_events(self):
        __tracebackhide__ = True
        _assert_retry(lambda: len(self.events) > 0)


@pytest.fixture
def fixture(tmp_path: Path):
    return Fixture(tmp_path / 'folder1')


def test_watch_non_existing_folder__should_not_fail(fixture: Fixture):
    fixture.target.watch_directory()


def test_watch_existing_folder_should_yield_some_events(fixture: Fixture):
    # GIVEN
    fixture.path.mkdir()
    fixture.target.watch_directory()

    # WHEN
    file_path = fixture.path / 'test_file.txt'
    file_path.touch()

    # THEN
    fixture.assert_has_events()


def test_non_existing_folder_than_created_should_yield_some_events(fixture: Fixture):
    # GIVEN
    fixture.target.watch_directory()

    # WHEN
    # at this point, we are in polling mode, so we need a delay to wait for the AnyObserver to start
    fixture.path.mkdir()
    _assert_retry(lambda: fixture.target.active)
    (fixture.path / 'file1.txt').touch()

    # WHEN
    fixture.assert_has_events()


def test_disappear_and_reappear_folder_should_yield_some_events(fixture: Fixture):
    # GIVEN
    fixture.path.mkdir()
    fixture.target.watch_directory()

    # WHEN
    fixture.path.rmdir()
    _assert_retry(lambda: not fixture.target.active)
    fixture.path.mkdir()
    _assert_retry(lambda: fixture.target.active)
    fixture.events.clear()

    (fixture.path / 'file1.txt').touch()

    # THEN
    fixture.assert_has_events()


def _assert_retry(condition):
    __tracebackhide__ = True
    [sleep(0.1) for _ in range(5 * timeout_multiplier()) if not condition()]
    assert condition(), 'wait_condition timeout'
