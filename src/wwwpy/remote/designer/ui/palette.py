from __future__ import annotations

import logging

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.common.injectorlib import inject
from wwwpy.remote import dict_to_js
from wwwpy.remote.component import get_component
from wwwpy.remote.designer.ui.design_aware import DesignAware
from wwwpy.remote.designer.ui.intent import Intent, IntentChangedEvent, IntentEvent
from wwwpy.remote.designer.ui.intent_manager import IntentManager
from wwwpy.remote.jslib import get_deepest_element

logger = logging.getLogger(__name__)


class _PaletteIntentAware(DesignAware):

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        return palette_find_indent(hover_event.deep_target)


def palette_find_indent(target: js.Element) -> Intent | None:
    res = target.closest(PaletteItemComponent.component_metadata.tag_name)
    if res:
        comp: PaletteItemComponent = get_component(res)
        return comp.intent
    return None


_palette_design_aware = _PaletteIntentAware()


def extension_point_register():
    DesignAware.EP_REGISTRY.register(_palette_design_aware)


def extension_point_unregister():
    DesignAware.EP_REGISTRY.unregister(_palette_design_aware)


class PaletteComponent(wpc.Component, tag_name='wwwpy-palette'):
    _item_container: js.HTMLDivElement = wpc.element()
    intent_manager: IntentManager = inject()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<div class="container">
    <div class="palette" data-name="_item_container">
    </div>
</div>
"""
        self.element.shadowRoot.innerHTML += _css_styles

        def ace(e: IntentChangedEvent):
            if e.old is not None:
                intent = self._action2item.get(id(e.old), None)
                if intent:
                    intent.selected = False
            if e.new is not None:
                intent = self._action2item.get(id(e.new), None)
                if intent:
                    intent.selected = True

        self._action2item = {}

        self._on_action_changed_event = ace
        self._palette_design_aware = _PaletteIntentAware()
        self._on_identify_event = lambda e: e.set_action(_find_palette_action(e.js_event))

    def connectedCallback(self):
        self.intent_manager.on(IntentChangedEvent).add(self._on_action_changed_event)

    def disconnectedCallback(self):
        self.intent_manager.on(IntentChangedEvent).remove(self._on_action_changed_event)

    def add_intent(self, intent: Intent) -> PaletteItemComponent:
        """Add an item to the palette."""
        item = PaletteItemComponent()
        item.intent = intent
        item.label = intent.label
        item.element.classList.add('palette-item')
        self._item_container.appendChild(item.element)
        self._action2item[id(intent)] = item
        # item.element.addEventListener('click', create_proxy(lambda e: self.intent_manager._action_item_click(item)))
        return item


class PaletteItemComponent(wpc.Component, tag_name='palette-item-icon'):
    _label: js.HTMLLabelElement = wpc.element()
    intent: Intent

    # override magic method so the f strings get a nice representation
    def __repr__(self):
        return f'{self.__class__.__name__}({self.label})'

    def init_component(self):
        # language=html
        self.element.innerHTML = """
 <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round"
      stroke-linejoin="round">
     <rect x="3" y="8" width="18" height="8" rx="2" ry="2"></rect>
     <line x1="12" y1="12" x2="12" y2="12"></line>
 </svg>
 <label data-name="_label" style="display: block; text-align: center"></label>
 </div>
 </div> 
"""
        self.intent: Intent = None

    @property
    def label(self) -> str:
        return self._label.innerText

    @label.setter
    def label(self, value: str):
        self._label.innerText = value

    @property
    def selected(self) -> bool:
        return self.element.classList.contains('selected')

    @selected.setter
    def selected(self, value: bool):
        if value:
            self.element.classList.add('selected')
        else:
            self.element.classList.remove('selected')


# class ActionManager:
#     """A class to manage interaction and events to handle, drag & drop, element selection, move element."""
#
#     def __init__(self):
#         self.pointer_manager: PointerManager[Action] = PointerManager()
#         self.pointer_manager.on(IdentifyEvent).add(lambda e: e.set_action(_find_palette_action(e.js_event)))
#         self.install = self.pointer_manager.install
#         self.uninstall = self.pointer_manager.uninstall
#         self.on = self.pointer_manager.on
#
#     @property
#     def selected_action(self) -> Action | None:
#         return self.pointer_manager.selected_action
#
#     @selected_action.setter
#     def selected_action(self, value: Action | None):
#         self.selected_action = value


def _find_palette_action(event: js.Event) -> Intent | None:
    target = get_deepest_element(event.clientX, event.clientY)
    if target is None:  # tests missing. It looks like it happens when the mouse exit the viewport or moves on the scrollbar
        return None
    # logger.debug(f'_find_palette_item target={_pretty(target)}')
    import wwwpy.remote.designer.ui.palette as palette
    res = target.closest(palette.PaletteItemComponent.component_metadata.tag_name)
    if res:
        comp: PaletteItemComponent = get_component(res)
        return comp.intent
    return None


# language=html
_css_styles = """<style>
    :host {
        --primary-color: #6366f1;
        --primary-hover: #818cf8;
        --secondary-color: #4f46e5;
        --border-color: #4b5563;
        --shadow-color: rgba(0, 0, 0, 0.3);
        --workspace-bg: #1e1e2e;
        --palette-bg: #27293d;
        --text-color: #e2e8f0;
        --item-bg: #2d3748;
        --item-hover-bg: #3a4358;
        --selected-bg: #4c1d95;
        --selected-border: #8b5cf6;
    }

    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        height: 100vh;
        background-color: #111827;
        color: var(--text-color);
    }

    .header {
        background-color: var(--primary-color);
        color: white;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 5px var(--shadow-color);
    }

    .container {
        display: flex;
        flex: 1;
        overflow: hidden;
    }

    .palette {
        width: 220px;
        background-color: var(--palette-bg);
        padding: 1rem;
        border-right: 1px solid var(--border-color);
        box-shadow: 2px 0 5px var(--shadow-color);
        overflow-y: auto;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        align-content: start;
        height: fit-content;
        max-height: 100%;
    }

    .workspace {
        flex: 1;
        background-color: var(--workspace-bg);
        padding: 2rem;
        overflow: auto;
        position: relative;
    }

    .palette-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 0.75rem 0.5rem;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        user-select: none;
        background-color: var(--item-bg);
        font-size: 12px;
        color: var(--text-color);
        touch-action: none;
    }

    .palette-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 3px 5px var(--shadow-color);
        background-color: var(--item-hover-bg);
    }

    .palette-item.selected {
        background-color: var(--selected-bg);
        border: 1px solid var(--selected-border);
        box-shadow: 0 0 0 2px var(--selected-border), 0 0 12px rgba(139, 92, 246, 0.5);
        position: relative;
        transform: scale(1.05);
    }

    .palette-item svg {
        margin-bottom: 8px;
        width: 36px;
        height: 36px;
    }

    .log-panel {
        padding: 1rem;
        background-color: #2c3e50;
        color: #ecf0f1;
        max-height: 150px;
        overflow-y: auto;
        font-family: monospace;
    }

    .log-entry {
        margin-bottom: 5px;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 5px;
    }

    .log-entry:last-child {
        border-bottom: none;
    }

    /* Element previews in workspace */
    .element-preview {
        position: absolute;
        border: 2px dashed var(--primary-color);
        padding: 5px;
        border-radius: 4px;
        background-color: rgba(52, 152, 219, 0.1);
        min-width: 100px;
        min-height: 30px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        color: #666;
    }

    /* Dragging Element Preview */
    .dragging-element {
        position: absolute;
        pointer-events: none;
        opacity: 0.8;
        z-index: 1000;
        transform: translate(-50%, -50%);
        background-color: var(--selected-bg);
        border: 1px solid var(--selected-border);
        padding: 5px 10px;
        border-radius: 4px;
        color: white;
        font-size: 12px;
    }
</style> 
              """


def _pretty(node):
    if node is None:
        return 'None'
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)
