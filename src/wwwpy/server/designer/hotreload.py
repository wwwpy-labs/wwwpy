from pathlib import Path
from typing import List

from wwwpy.common.filesystem import sync


class Hotreload:

    def __init__(self, directory: Path,
                 server_packages: List[str], remote_packages: List[str],
                 server_unload_func, remote_notify_func
                 ):
        self.directory = directory
        self.server_packages = server_packages
        self.remote_packages = remote_packages
        self._server_unload_func = server_unload_func
        self._remote_notify_func = remote_notify_func

    def process_events(self, events: List[sync.Event]):
        self._remote_notify_func(events)
        self._server_unload_func()
