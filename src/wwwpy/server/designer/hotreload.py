import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Callable

from wwwpy.common.files import extension_blacklist, directory_blacklist
from wwwpy.common.filesystem import sync
from wwwpy.common.filesystem.sync import sync_delta2, Sync
from wwwpy.remote.designer.rpc import DesignerRpc
from wwwpy.server.filesystem_sync.watchdog_debouncer import WatchdogDebouncer
from wwwpy.websocket import WebsocketPool

logger = logging.getLogger(__name__)

sync_impl: Sync = sync_delta2


def start_hotreload(directory: Path, websocket_pool: WebsocketPool,
                    server_packages, remote_packages):
    def server_unload_func():
        do_unload_for(directory, server_packages)

    def remote_notify_func(events: List[sync.Event]):
        process_remote_events(directory, websocket_pool, events)

    hr = Hotreload(directory, server_packages, remote_packages, server_unload_func, remote_notify_func)
    _watch_filesystem_change(directory, hr.process_events)


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


def process_remote_events(directory: Path, websocket_pool: WebsocketPool, events: List[sync.Event]):
    try:
        payload = sync_impl.sync_source(directory, events)
        for client in websocket_pool.clients:
            remote_rpc = client.rpc(DesignerRpc)
            remote_rpc.hotreload_notify_changes(payload)
    except:
        # we could send a sync_init
        import traceback
        logger.error(f'_on_remote_events 1 {traceback.format_exc()}')


def do_unload_for(directory, server_packages: List[str]):
    for p in server_packages:
        package_directory = directory / p.replace('.', '/')
        if package_directory:
            try:
                import wwwpy.common.reloader as reloader
                reloader.unload_path(str(package_directory))
            except:
                # we could send a sync_init
                import traceback
                logger.error(f'_hotreload_server {traceback.format_exc()}')


def _watch_filesystem_change(directory: Path, callback: Callable[[List[sync.Event]], None]):
    def on_sync_events(events: List[sync.Event]):
        try:
            # oh, boy. When a .py file is saved it fires the first hot reload. Then, when that file is loaded
            # the python updates the __pycache__ files, firing another (unwanted) reload: the first was enough!
            filtered_events = _filter_events(events, directory)
            if len(filtered_events) > 0:
                callback(filtered_events)
        except:
            import traceback
            logger.error(f'_watch_filesystem_change {traceback.format_exc()}')

    handler = WatchdogDebouncer(directory, timedelta(milliseconds=100), on_sync_events)
    handler.watch_directory()


def _filter_events(events: List[sync.Event], directory: Path) -> List[sync.Event]:
    def reject(e: sync.Event) -> bool:
        src_path = Path(e.src_path)
        if src_path.suffix in extension_blacklist:
            return True
        p = src_path.relative_to(directory)
        for part in p.parts:
            if part in directory_blacklist:
                return True
        return False

    result = [e for e in events if not reject(e)]
    _print_events(result, directory, len(events) - len(result))
    return result


def _print_events(events: List[sync.Event], root_dir: Path, blacklisted_count: int):
    def accept(e: sync.Event) -> bool:
        bad = e.is_directory and e.event_type == 'modified'
        return not bad

    def to_str(e: sync.Event) -> str:
        def rel(path: str) -> str:
            return str(Path(path).relative_to(root_dir))

        dest_path = rel(e.dest_path) if e.dest_path else ''
        src_path = rel(e.src_path)
        return src_path if dest_path == '' else f'{src_path} -> {dest_path}'

    summary = list(set(to_str(e) for e in events if accept(e)))
    blacklist_applied = f' [{blacklisted_count} blacklisted events]' if blacklisted_count > 0 else ''
    logger.info(f'Hotreload events: {len(events)}. Changes summary: {summary}{blacklist_applied}')
