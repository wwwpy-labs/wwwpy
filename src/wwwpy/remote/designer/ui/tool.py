from __future__ import annotations

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly
from wwwpy.remote import component as wpc


class Tool(wpc.Component, auto_define=False):
    def set_reference_geometry(self, rect: RectReadOnly):
        """Set the geometry of the element that the tool is attached to."""
