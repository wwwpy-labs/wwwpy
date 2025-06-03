import logging

import wwwpy.remote.component as wpc
import wwwpy.remote.designer.ui.accordion_components  # noqa
import wwwpy.remote.designer.ui.comp_structure  # noqa
from wwwpy.common.designer.canvas_selection import CanvasSelection, CanvasSelectionChangeEvent
from wwwpy.common.designer.element_library import element_library
from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer.ui import pushable_sidebar, palette
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent
from wwwpy.remote.designer.ui.intent_select_element import SelectElementIntent
from wwwpy.remote.designer.ui.property_editor import PropertyEditor
from wwwpy.remote.designer.ui.system_tools.system_tools_component import SystemToolsComponent

logger = logging.getLogger(__name__)


class NewToolbox(wpc.Component, tag_name='wwwpy-new-toolbox'):
    _sidebar: pushable_sidebar.PushableSidebar = wpc.element()
    _palette: palette.PaletteComponent = wpc.element()
    _property_editor: PropertyEditor = wpc.element()
    _system_tools: SystemToolsComponent = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<pushable-sidebar data-name="_sidebar" position="right" width="300px">
    <wwwpy-accordion-section expanded>
        <div slot="header">Add Components</div>
        <wwwpy-palette data-name="_palette" style="height: 300px; display: flex"></wwwpy-palette>
    </wwwpy-accordion-section>
    <wwwpy-accordion-section expanded>
        <div slot="header">Structure</div>
        <wwwpy-comp-structure style="height: 250px; display: flex; overflow: scroll"></wwwpy-comp-structure>
    </wwwpy-accordion-section>
    <wwwpy-accordion-section expanded>
        <div slot="header">Attributes/Events</div>
        <wwwpy-property-editor data-name="_property_editor" style="height: 250px; display: flex; overflow: scroll"></wwwpy-property-editor>
    </wwwpy-accordion-section>
    <wwwpy-accordion-section expanded>
        <div slot="header">System Tools</div>
        <wwwpy-system-tools data-name="_system_tools"></wwwpy-system-tools>
    </wwwpy-accordion-section>
</pushable-sidebar>
        """
        self._setup_palette()
        self._setup_property_editor()

    def _setup_palette(self):
        self._palette.add_intent(SelectElementIntent())
        for ei in element_library().elements:
            if ei.tag_name.startswith('sl-'):
                continue
            self._palette.add_intent(AddElementIntent(ei.tag_name, element_def=ei))

    def _setup_property_editor(self):
        def _csce(event: CanvasSelectionChangeEvent):
            logger.debug(f'canvas selection changed: {event}')
            self._property_editor.selected_element_path = event.new

        canvas_selection = injector.get(CanvasSelection)
        canvas_selection.on_change.add(_csce)

    @property
    def visible(self) -> bool:
        return self._sidebar.state != 'hidden'

    @visible.setter
    def visible(self, value: bool):
        self._sidebar.state = 'expanded' if value else 'hidden'
