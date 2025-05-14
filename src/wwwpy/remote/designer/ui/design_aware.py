from __future__ import annotations

from wwwpy.common.extension_point import ExtensionPointRegistry, ep_registry
from wwwpy.remote.designer.ui.intent import HoverEvent


class DesignAware:
    EP_LIST: ExtensionPointRegistry[DesignAware] = ep_registry()

    def is_designer(self, hover_event: HoverEvent) -> bool | None:
        return False


def is_designer(hover_event: HoverEvent) -> bool:
    for ep in DesignAware.EP_LIST:
        if ep.is_designer(hover_event) is True:
            return True
    return False
