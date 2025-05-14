from __future__ import annotations

import js

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js


class HelpIcon(wpc.Component, tag_name='wwwpy-help-icon'):
    _link: js.HTMLElement = wpc.element()
    href: str = wpc.attribute()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>        
 .help-icon {
            width: 18px;
            height: 18px;
            vertical-align: middle;
            margin-left: 5px;
        }
</style>        
<svg xmlns="http://www.w3.org/2000/svg" style="display: none;">
    <symbol id="help-icon" viewBox="0 0 18 18">
        <circle cx="9" cy="9" r="8" fill="#007bff"/>
        <text x="9" y="9" fill="white" text-anchor="middle" dominant-baseline="central" font-weight="bold" font-size="12">?</text>
    </symbol>
</svg>   
<a data-name="_link" style="text-decoration: none" target="_blank">
<svg class="help-icon"><use href="#help-icon"/></svg></a>
"""
        self._update_href()

    def _link__click(self, event: js.MouseEvent):
        event.stopPropagation()
        if not self.href:
            event.preventDefault()

    def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
        if name == 'href':
            self._update_href()

    def _update_href(self):
        self._link.href = self.href

    @property
    def visible(self):
        return self.element.style.visibility != 'hidden'

    @visible.setter
    def visible(self, value):
        self.element.style.visibility = 'visible' if value else 'hidden'
