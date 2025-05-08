from __future__ import annotations

import js


# todo make this a Component with no registration
class Tool:
    def set_reference_geometry(self, rect: js.DOMRectReadOnly):
        """Set the geometry of the element that the tool is attached to."""
