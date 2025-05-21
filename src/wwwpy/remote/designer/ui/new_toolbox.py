import logging

import wwwpy.remote.component as wpc
import wwwpy.remote.designer.ui.accordion_components  # noqa
from wwwpy.common.designer.element_library import element_library
from wwwpy.remote.designer.ui import pushable_sidebar, palette
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent
from wwwpy.remote.designer.ui.intent_select_element import SelectElementIntent

logger = logging.getLogger(__name__)


class NewToolbox(wpc.Component, tag_name='wwwpy-new-toolbox'):
    _sidebar: pushable_sidebar.PushableSidebar = wpc.element()
    _palette: palette.PaletteComponent = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<pushable-sidebar data-name="_sidebar" position="left" width="300px">
    <wwwpy-accordion-section expanded>
        <div slot="header">Add Components</div>
        <wwwpy-palette data-name="_palette" style="height: 300px; display: flex"></wwwpy-palette>
    </wwwpy-accordion-section>
    <wwwpy-accordion-section expanded>
        <div slot="header">Structure</div>
        <wwwpy-comp-tree style="height: 250px; display: flex; overflow: scroll"></wwwpy-comp-tree>
</pushable-sidebar>
        """
        self._palette.add_intent(SelectElementIntent())
        for ei in element_library().elements:
            if ei.tag_name.startswith('sl-'):
                continue
            self._palette.add_intent(AddElementIntent(ei.tag_name, element_def=ei))
