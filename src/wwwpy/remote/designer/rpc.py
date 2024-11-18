from pathlib import Path
from typing import List, Any

from wwwpy.common import modlib, files


class DesignerRpc:
    # todo deprecated
    def package_file_changed_sync(self, package_name: str, events: List[Any]):
        from wwwpy.common.filesystem.sync import sync_delta2
        from wwwpy.common.filesystem.sync import Sync
        sync_impl: Sync = sync_delta2
        directory = modlib._find_package_directory(package_name)
        sync_impl.sync_target(directory, events)

        from wwwpy.remote.browser_main import _reload
        _reload()

    def hotreload_notify_changes(self, events: List[Any]):
        from wwwpy.common.filesystem.sync import sync_delta2
        from wwwpy.common.filesystem.sync import Sync
        sync_impl: Sync = sync_delta2
        directory = Path(files._bundle_path)
        sync_impl.sync_target(directory, events)

        from wwwpy.remote.browser_main import _reload
        _reload()
