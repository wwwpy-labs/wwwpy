from pathlib import Path
from typing import List, Any

from wwwpy.common import files


class DesignerRpc:

    def hotreload_notify_changes(self, do_reload: bool, events: List[Any]):
        directory = Path(files._bundle_path)

        from wwwpy.common.filesystem.sync import Sync, sync_delta2
        sync_impl: Sync = sync_delta2
        sync_impl.sync_target(directory, events)
        if do_reload:
            self.hotreload_do()

    def hotreload_do(self):
        from wwwpy.remote.browser_main import _reload
        _reload()
