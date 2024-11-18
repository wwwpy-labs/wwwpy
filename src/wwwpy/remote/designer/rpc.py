from pathlib import Path
from typing import List, Any

from wwwpy.common import files


class DesignerRpc:

    def hotreload_notify_changes(self, events: List[Any]):
        directory = Path(files._bundle_path)

        from wwwpy.common.filesystem.sync import Sync, sync_delta2
        sync_impl: Sync = sync_delta2
        sync_impl.sync_target(directory, events)

        from wwwpy.remote.browser_main import _reload
        _reload()
