from __future__ import annotations

import dataclasses
import inspect
import logging
from enum import Enum
from functools import cached_property

import js

import wwwpy.remote.component as wpc
import wwwpy.remote.designer.ui.new_toolbox  # noqa
from wwwpy.common import modlib
from wwwpy.common.designer.comp_info import iter_comp_info_folder, CompInfo, LocatorNode, ComponentDef
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.common.eventbus import EventBus
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_js
from wwwpy.remote.component import get_component
from wwwpy.remote.designer.dev_mode_events import AfterDevModeShow
from wwwpy.remote.designer.ui.design_aware import DesignAware
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent, IntentChangedEvent
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent
from wwwpy.remote.designer.ui.intent_manager import IntentManager
from wwwpy.remote.designer.ui.locator_event import LocatorEvent
from wwwpy.remote.jslib import get_deepest_element, closest_across_shadow

logger = logging.getLogger(__name__)


class HeaderClick(Enum):
    MARKER = 'MARKER'
    TEXT = 'TEXT'


class _DesignAware(DesignAware):

    def find_intent(self, hover_event: IntentEvent) -> Intent | None:
        target = hover_event.deep_target
        # def is_container(element: js.Element) -> bool:
        #     return element.tagName.lower() == AddUserComponentIntentUI.component_metadata.tag_name.lower()
        #
        # is_cont = is_contained(target, is_container)
        # if is_cont:
        #     logger.warning(f'find_intent: is_contained {target.tagName} {target.className}')
        # return

        if not target: return None
        # res = target.closest(AddUserComponentIntentUI.component_metadata.tag_name)
        res = closest_across_shadow(target, AddUserComponentIntentUI.component_metadata.tag_name)
        if not res: return None
        comp = get_component(res, AddUserComponentIntentUI)
        if not comp: return None
        return comp.intent

        # comp_tree_item: CompStructureItem = wpc.get_component(res)
        # x = hover_event.js_event.clientX - comp_tree_item._summary.getBoundingClientRect().left
        # if x < 20: return None
        # return comp_tree_item.add_intent

    # def is_selectable_js(self, js_event: js.PointerEvent) -> bool | None:
    #     w = _click_where(js_event)
    #     if w == HeaderClick.TEXT:
    #         return True
    #     return None
    def is_selectable_le(self, locator_event: LocatorEvent) -> bool | None:
        if locator_event.locator.match_component_type(AddUserComponentIntentUI):
            logger.warning(f'is_selectable_le: click on summary')
            return None
        struct_item = _get_comp_structure_item(locator_event.main_element)
        if struct_item:
            if locator_event.main_element == struct_item._summary:
                logger.warning(f'is_selectable_le: click on summary')
                return None
            l = locator_event.locator
            logger.warning(f'is_selectable_le: {l.tag_name} {l.class_name}')
            left = locator_event.main_element.getBoundingClientRect().left
            return locator_event.main_xy[0] - left > 20
        return None

    def locator_event_transformer(self, locator_event: LocatorEvent) -> LocatorEvent | None:
        if not isinstance(locator_event, LocatorEvent):
            raise TypeError(f'Expected LocatorEvent, got {type(locator_event)}')
        locator_node = _get_locator_node(locator_event)
        if locator_node:
            logger.warning(f'locator_event_transformer: {locator_node.locator}')
            new_locator_event = dataclasses.replace(locator_event, locator=locator_node.locator)
            return new_locator_event
        return None


def _get_locator_node(locator_event: LocatorEvent) -> LocatorNode | None:
    if locator_event.locator.match_component_type(CompStructureItem):
        if hasattr(locator_event.main_element, '_locator_node'):
            locator_node: LocatorNode = locator_event.main_element._locator_node
            return locator_node
    return None


def _set_locator_node(element: js.Element, locator_node: LocatorNode):
    element._locator_node = locator_node


# class _PointerEventInfo:
#     element: js.Element
#     comp_tree_item: CompStructureItem
def _get_comp_structure_item(contained_element: js.Element) -> CompStructureItem | None:
    res = contained_element.closest(CompStructureItem.component_metadata.tag_name)
    if not res: return None
    comp_tree_item: CompStructureItem = wpc.get_component(res, CompStructureItem)
    return comp_tree_item


def _click_where(js_event: js.PointerEvent) -> HeaderClick | None:
    target = get_deepest_element(js_event.clientX, js_event.clientY)
    if not target: return None
    comp_tree_item = _get_comp_structure_item(target)
    x = js_event.clientX - comp_tree_item._summary.getBoundingClientRect().left
    # if x < 20:
    #     return HeaderClick.MARKER
    # else:
    #     return HeaderClick.TEXT
    return HeaderClick.TEXT if x > 20 else HeaderClick.MARKER


_design_aware = _DesignAware()


class CompStructure(wpc.Component, tag_name='wwwpy-comp-structure'):
    _div: js.HTMLDivElement = wpc.element()
    _eventbus: EventBus = injector.field()
    span1: js.HTMLElement = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>
    
    details > details {
        margin-left: 1em;
    }
    
    .no-marker > summary {
      list-style: none;
      padding-left: 0.5em;
    }
    .no-marker > summary::-webkit-details-marker {
      display: none;
    }
</style>
<div>
<div data-name="span1">Create new Component</div>
<div data-name="_div"></div>
</div>
        """
        self._subscription = None

    def connectedCallback(self):
        self._subscription = self._eventbus.subscribe(self._scan_for_components, on=AfterDevModeShow)
        DesignAware.EP_REGISTRY.unregister(_design_aware)
        DesignAware.EP_REGISTRY.register(_design_aware)

    def disconnectedCallback(self):
        self._subscription.unsubscribe()
        self._subscription = None
        DesignAware.EP_REGISTRY.unregister(_design_aware)

    def _scan_for_components(self, _):
        logger.debug('scan_for_components')
        self._div.innerHTML = ''
        rem = modlib._find_package_directory('remote')
        if not rem:
            return
        for ci in iter_comp_info_folder(rem, 'remote'):
            cti = CompStructureItem()
            cti.set_comp_info(ci)
            self._div.appendChild(cti.element)

    async def span1__click(self, event):
        logger.debug(f'{inspect.currentframe().f_code.co_name} event fired %s', event)
        if js.window.confirm('Add new component file?\nIt will be added to your "remote" folder.'):
            from wwwpy.server.designer import rpc
            res = await rpc.add_new_component()
            js.window.alert(res)
    


class CompStructureItem(wpc.Component, tag_name='wwwpy-comp-structure-item'):
    comp_info: CompInfo
    _details: js.HTMLElement = wpc.element()
    _summary: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<details data-name="_details">
    <summary data-name="_summary"></summary>
</details>
        """

    def set_comp_info(self, ci: CompInfo):
        self.comp_info = ci

        self._summary.innerText = ci.path.name + ' / ' + ci.class_name
        self._summary.appendChild(self.intent_ui.element)

        def rec(ln_list: list[LocatorNode], elem: js.Element, level):
            for child in ln_list:
                cst_node = child.cst_node
                data_name = cst_node.attributes.get('data-name', None) or ''
                dn = '' if not data_name else f' - {data_name} '
                content = cst_node.content or ''

                if content:
                    escape_table = str.maketrans({
                        '\r': ' ',
                        '\n': ' ',
                        '\t': ' ',
                    })
                    content = content.translate(escape_table)
                    max_content = 15
                    if len(content) > max_content:
                        content = content[:max_content] + '…'
                    content = f' / {content}'

                summary_text = f'{cst_node.tag_name}{dn}{content}'

                # language=html
                html = """<details open><summary></summary></details>"""
                ch = js.document.createRange().createContextualFragment(html)
                elem.appendChild(ch)
                details = elem.lastElementChild
                if len(cst_node.children) == 0:
                    details.classList.add('no-marker')
                else:
                    rec(child.children, details, level + 1)
                summary = details.firstElementChild
                _set_locator_node(summary, child)
                summary.innerText = summary_text

        try:
            rec(ci.locator_root.children, self._details, 1)
        except:
            logger.exception('Error in CompTreeItem.set_comp_info')
            self._details.innerText = 'Error in CompTreeItem.set_comp_info'

    @cached_property
    def add_intent(self) -> Intent:
        tag_name = self.comp_info.tag_name
        label = f'Add {tag_name}'
        intent = AddElementIntent(label)
        element_def_min: ElementDefBase = ComponentDef(tag_name, self.comp_info.class_full_name, self.comp_info)
        intent.element_def = element_def_min
        return intent

    @cached_property
    def intent_ui(self) -> AddUserComponentIntentUI:
        intent_ui = AddUserComponentIntentUI()
        intent_ui.intent = self.add_intent
        return intent_ui


class AddUserComponentIntentUI(wpc.Component):
    intent: Intent
    _intent_manager: IntentManager = injector.field()
    _span: js.Element = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
        
<style>
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
    .intent-ui {
        align-items: center;
        justify-content: center;
        vertical-align: center;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s ease;
        user-select: none;
        background-color: var(--item-bg);
        color: var(--text-color);
        touch-action: none;
    }

    .intent-ui:hover {
       transform: translateY(-2px);
        box-shadow: 0 3px 5px var(--shadow-color);
        background-color: var(--item-hover-bg);
    }

    .intent-ui.selected {
        background-color: var(--selected-bg);
        border: 1px solid var(--selected-border);
        box-shadow: 0 0 0 2px var(--selected-border), 0 0 12px rgba(139, 92, 246, 0.5);
        position: relative;
        transform: scale(1.05);
    }
</style>
 <svg data-name="_span" class='intent-ui' xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor" stroke-width="2" stroke-linecap="round"
      stroke-linejoin="round">
     <rect x="3" y="8" width="18" height="8" rx="2" ry="2"></rect>
     <line x1="12" y1="12" x2="12" y2="12"></line>
 </svg>
"""
        self.intent: Intent = None

    def connectedCallback(self):
        self._intent_manager.on(IntentChangedEvent).add(self._on_intent_changed_event)

    def disconnectedCallback(self):
        self._intent_manager.on(IntentChangedEvent).remove(self._on_intent_changed_event)

    def _on_intent_changed_event(self, event: IntentChangedEvent):
        if not self.intent:
            return
        old = self.selected
        self.selected = event.new == self.intent
        if old != self.selected:
            logger.warning(f'_on_intent_changed_event: {event} selected: {self.selected}')

    @property
    def selected(self) -> bool:
        return self._span.classList.contains('selected')

    @selected.setter
    def selected(self, value: bool):
        if value:
            self._span.classList.add('selected')
        else:
            self._span.classList.remove('selected')
