import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Callable, Set

from wwwpy.common.files import extension_blacklist, directory_blacklist
from wwwpy.common.filesystem import sync
from wwwpy.common.filesystem.sync import sync_delta2, Sync, event_rebase
from wwwpy.remote.designer.rpc import DesignerRpc
from wwwpy.server.filesystem_sync.watchdog_debouncer import WatchdogDebouncer
from wwwpy.websocket import WebsocketPool, PoolEvent

logger = logging.getLogger(__name__)

sync_impl: Sync = sync_delta2


def _warning_on_multiple_clients(websocket_pool: WebsocketPool):
    def pool_before_change(event: PoolEvent):
        client_count = len(websocket_pool.clients)
        if client_count > 1:
            logger.warning(f'WARNING: more than one client connected, total={client_count}')
        else:
            logger.warning(f'Connected client count: {client_count}')

    websocket_pool.on_after_change.append(pool_before_change)


def start_hotreload(directory: Path, websocket_pool: WebsocketPool,
                    server_folders: Set[str], remote_folders: Set[str]):
    remote_set = {directory / d for d in remote_folders}
    server_set = {directory / d for d in server_folders}

    def process_events(events: List[sync.Event]):
        remote_events = event_rebase.filter_by_directory(events, remote_set)
        if len(remote_events) > 0:
            _print_events('remote', remote_events, directory)
            process_remote_events(directory, websocket_pool, remote_events)

        server_events = event_rebase.filter_by_directory(events, server_set)
        if len(server_events) > 0:
            _print_events('server', server_events, directory)
            do_unload_for(directory, server_folders)

    _watch_filesystem_change(directory, process_events)


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


def do_unload_for(directory, server_folders: Set[str]):
    for p in server_folders:
        package_directory = directory / p
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
    return result


def _print_events(label: str, events: List[sync.Event], root_dir: Path):
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
    logger.info(f'Hotreload {label} events: {len(events)}. Changes summary: {summary}')
