from __future__ import annotations

import logging
from enum import Enum
from functools import cached_property

import js

import wwwpy.remote.component as wpc
import wwwpy.remote.designer.ui.new_toolbox  # noqa
from wwwpy.common import modlib
from wwwpy.common.designer.comp_info import iter_comp_info_folder, CompInfo
from wwwpy.common.designer.element_library import ElementDefBase
from wwwpy.common.designer.html_parser import CstTree
from wwwpy.common.eventbus import EventBus
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.dev_mode_events import AfterDevModeShow
from wwwpy.remote.designer.ui.design_aware import DesignAware
from wwwpy.remote.designer.ui.intent import IntentEvent, Intent
from wwwpy.remote.designer.ui.intent_add_element import AddElementIntent

logger = logging.getLogger(__name__)


class HeaderClick(Enum):
    MARKER = 'MARKER'
    TEXT = 'TEXT'


class _DesignAware(DesignAware):

    def find_intent(self, hover_event: IntentEvent):
        # where = _click_where(hover_event)
        target = hover_event.deep_target
        if not target: return None
        res = target.closest(CompTreeItem.component_metadata.tag_name)
        if not res: return None

        comp_tree_item: CompTreeItem = wpc.get_component(res)
        x = hover_event.js_event.clientX - comp_tree_item._summary.getBoundingClientRect().left
        if x < 20: return None
        return comp_tree_item.add_intent


# def _click_where(hover_event: IntentEvent) -> HeaderClick | None:
#     target = hover_event.deep_target
#     if not target: return None
#     res = target.closest(CompTreeItem.component_metadata.tag_name)
#     if not res: return None
#
#     comp_tree_item: CompTreeItem = wpc.get_component(res)
#     x = hover_event.js_event.clientX - comp_tree_item._summary.getBoundingClientRect().left
#     # if x < 20:
#     #     return HeaderClick.MARKER
#     # else:
#     #     return HeaderClick.TEXT
#     return HeaderClick.TEXT if x > 20 else HeaderClick.MARKER


_design_aware = _DesignAware()


class CompTree(wpc.Component, tag_name='wwwpy-comp-tree'):
    _div: js.HTMLDivElement = wpc.element()
    _eventbus: EventBus = injector.field()

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

<div data-name="_div"></div>
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
        logger.warning('scan_for_components')
        self._div.innerHTML = ''
        rem = modlib._find_package_directory('remote')
        if not rem:
            return
        for ci in iter_comp_info_folder(rem, 'remote'):
            cti = CompTreeItem()
            cti.set_comp_info(ci)
            self._div.appendChild(cti.element)


class CompTreeItem(wpc.Component, tag_name='wwwpy-comp-tree-item'):
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

        def rec(cst_tree: CstTree, elem: js.HTMLElement):
            for cst_node in cst_tree:
                summary = cst_node.tag_name
                dn = cst_node.attributes.get('data-name', None)
                if dn:
                    summary += f' / {dn}'

                # language=html
                html = f"""
<details open>
  <summary>{summary}</summary>              
</details>                
"""

                ch = js.document.createRange().createContextualFragment(html)

                elem.appendChild(ch)
                last_ch = elem.lastElementChild
                if len(cst_node.children) == 0:
                    last_ch.classList.add('no-marker')
                else:
                    rec(cst_node.children, last_ch)

        try:
            rec(ci.cst_tree, self._details)
        except:
            logger.exception('Error in CompTreeItem.set_comp_info')
            self._details.innerText = 'Error in CompTreeItem.set_comp_info'

    @cached_property
    def add_intent(self) -> Intent:
        tag_name = self.comp_info.tag_name
        label = f'Add {tag_name}'
        intent = AddElementIntent(label)
        element_def_min: ElementDefBase = ElementDefBase(tag_name, self.comp_info.class_full_name)
        intent.element_def = element_def_min
        return intent
