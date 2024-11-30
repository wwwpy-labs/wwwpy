from __future__ import annotations

import asyncio

import js

import wwwpy.remote.component as wpc
from wwwpy.common import files
from wwwpy.remote import dict_to_js, dict_to_py
from wwwpy.server.designer import rpc
from . import quickstart_ui
from .quickstart_ui import QuickstartUI
from .toolbox import ToolboxComponent


def show():
    js.document.body.append(DevModeComponent().element)


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class DevModeComponent(wpc.Component, tag_name='wwwpy-dev-mode-component'):
    toolbox: ToolboxComponent = wpc.element()
    quickstart: QuickstartUI | None = None

    @classproperty
    def instance(cls) -> DevModeComponent:  # noqa
        element = js.document.getElementsByTagName(DevModeComponent.component_metadata.tag_name)
        if element.length == 0:
            raise Exception('DevModeComponent is not available')
        first_element = element[0]
        component = wpc.get_component(first_element)
        if not isinstance(component, DevModeComponent):
            raise Exception(f'element is not a DevModeComponent: {dict_to_py(first_element)}')
        return component

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<wwwpy-toolbox data-name="toolbox"></wwwpy-toolbox>        
        """

        async def check_for_quickstart():
            if await rpc.quickstart_possible():
                self.quickstart = quickstart_ui.create()
                self.element.shadowRoot.append(self.quickstart.window.element)
                self.toolbox.visible = False

        asyncio.create_task(check_for_quickstart())
