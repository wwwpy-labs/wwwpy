from __future__ import annotations

from wwwpy.common.extension_point import ExtensionPointList
from wwwpy.common.injectorlib import inject, injector
from wwwpy.remote.designer.ui.intent import HoverEvent


def register_bindings():
    injector.bind(ExtensionPointList(), to=ExtensionPointList[DesignAware])


class DesignAware:
    EP_LIST: ExtensionPointList[DesignAware] = inject()

    def is_designer(self, hover_event: HoverEvent) -> bool | None:
        return False


def is_designer(hover_event: HoverEvent) -> bool:
    for ep in DesignAware.EP_LIST.extensions:
        if ep.is_designer(hover_event) is True:
            return True
    return False
