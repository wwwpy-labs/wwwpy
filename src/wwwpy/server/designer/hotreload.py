import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Callable

from wwwpy.common.files import extension_blacklist, directory_blacklist
from wwwpy.common.filesystem import sync
from wwwpy.common.filesystem.sync import sync_delta2, Sync
from wwwpy.remote.designer.rpc import DesignerRpc
from wwwpy.server.filesystem_sync.watchdog_debouncer import WatchdogDebouncer
from wwwpy.websocket import WebsocketPool, PoolEvent

logger = logging.getLogger(__name__)

sync_impl: Sync = sync_delta2


class Hotreload:

    def __init__(self, directory: Path):
        self.directory = directory

    def configure_server(self, hotreload_packages: list[str]):
        def on_change(events: List[sync.Event]):

            for p in hotreload_packages:
                directory = self.directory / p.replace('.', '/')
                if directory:
                    try:
                        import wwwpy.common.reloader as reloader
                        reloader.unload_path(str(directory))
                    except:
                        # we could send a sync_init
                        import traceback
                        logger.error(f'_hotreload_server {traceback.format_exc()}')

        _watch_filesystem_change_for_server(self.directory, on_change)

    def configure_remote(self, remote_packages: list[str], websocket_pool: WebsocketPool, ):
        directory = self.directory

        def on_sync_events(events: List[sync.Event]):
            try:
                filtered_events = _filter_events(events, directory)
                if len(filtered_events) > 0:
                    payload = sync_impl.sync_source(directory, filtered_events)
                    for client in websocket_pool.clients:
                        remote_rpc = client.rpc(DesignerRpc)
                        remote_rpc.hotreload_notify_changes(payload)
            except:
                # we could send a sync_init
                import traceback
                logger.error(f'on_sync_events 1 {traceback.format_exc()}')

        handler = WatchdogDebouncer(directory, timedelta(milliseconds=100), on_sync_events)
        handler.watch_directory()


def _watch_filesystem_change_for_server(directory: Path, callback: Callable[[List[sync.Event]], None]):
    def on_sync_events(events: List[sync.Event]):
        try:
            # oh, boy. When a .py file is saved it fires the first hot reload. Then, when that file is loaded
            # the python updates the __pycache__ files, firing another (unwanted) reload: the first was enough!
            filtered_events = _filter_events(events, directory)
            if len(filtered_events) > 0:
                callback(filtered_events)
        except:
            import traceback
            logger.error(f'_watch_filesystem_change_for_server {traceback.format_exc()}')

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


def _warning_on_multiple_clients(websocket_pool: WebsocketPool):
    def pool_before_change(event: PoolEvent):
        client_count = len(websocket_pool.clients)
        if client_count > 1:
            logger.warning(f'WARNING: more than one client connected, total={client_count}')
        else:
            logger.warning(f'Connected client count: {client_count}')

    websocket_pool.on_after_change.append(pool_before_change)


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
