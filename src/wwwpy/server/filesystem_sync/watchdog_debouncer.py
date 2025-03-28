import threading
from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import Callable, List

from watchdog.events import FileSystemEvent

from wwwpy.common.filesystem.sync import new_tmp_path
from wwwpy.common.filesystem.sync.event import Event
from wwwpy.server.filesystem_sync.any_observer import AnyObserver
from wwwpy.server.filesystem_sync.debouncer import Debouncer
from wwwpy.server.filesystem_sync.debouncer_thread import DebouncerThread


class WatchdogDebouncer(DebouncerThread):

    def __init__(self, path: Path, window: timedelta, callback: Callable[[List[Event]], None]):
        self._debouncer = Debouncer(window)
        super().__init__(self._debouncer, callback)

        def skip_open(event: FileSystemEvent):
            if event.event_type == 'opened' or event.event_type == 'closed_no_write':
                return
            if event.is_synthetic:
                return

            e = Event(event.event_type, event.is_directory, event.src_path, event.dest_path)
            self._debouncer.add_event(e)

        self._any_observer = AnyObserver(path, skip_open)

    @property
    def debouncer(self):
        return self._debouncer

    def start(self):
        self._any_observer.watch_directory()
        super().start()

    def stop(self):
        self._any_observer.stop()
        super().stop()

    def join(self):
        self._any_observer.join()
        super().join()

    def watch_directory(self):
        self.start()


def main():
    tmp_path = new_tmp_path()
    print(f'watching {tmp_path}')

    def print_events(events: List[Event]):
        print('=' * 20 + f' current thread name={threading.current_thread().name}')
        print(f'originals:')
        for e in events:
            print(f'  {e}')
        print('relative:')
        for e in events:
            e = e.relative_to(tmp_path)
            print(f'  {e}')
        print(f'len={len(events)}')

    WatchdogDebouncer(tmp_path, timedelta(milliseconds=100), print_events).start()

    while True:
        sleep(1)


if __name__ == '__main__':
    main()
