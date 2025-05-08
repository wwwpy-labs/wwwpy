from __future__ import annotations

from wwwpy.common.designer.ui.rect_readonly import RectReadOnly


# todo make this a Component with no registration
class Tool:
    def set_reference_geometry(self, rect: RectReadOnly):
        """Set the geometry of the element that the tool is attached to."""
