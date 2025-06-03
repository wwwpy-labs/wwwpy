from __future__ import annotations

import logging

import js

import wwwpy.remote.component as wpc
from wwwpy.common.asynclib import create_task_safe
from wwwpy.common.eventbus import EventBus
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_js
from wwwpy.server.designer import rpc
from . import quickstart_ui
from .new_toolbox import NewToolbox
from .quickstart_ui import QuickstartUI
from ..dev_mode_events import AfterDevModeShow

logger = logging.getLogger(__name__)


def show():
    instance = DevModeComponent.instance
    js.document.body.append(instance.element)
    injector.get(EventBus).publish(AfterDevModeShow())


class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()


class DevModeComponent(wpc.Component, tag_name='wwwpy-dev-mode-component'):
    toolbox: NewToolbox = wpc.element()
    quickstart: QuickstartUI | None = None
    _instance: DevModeComponent

    @classproperty
    def instance(cls) -> DevModeComponent:  # noqa
        try:
            _i = cls._instance
            logger.debug(f'instance found: {_i}')
        except AttributeError:
            _i = DevModeComponent()
            cls._instance = _i
            logger.debug(f'instance created: {_i}')
        return _i

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<wwwpy-new-toolbox data-name='toolbox'></wwwpy-new-toolbox>     
        """

    async def _connectedCallback_async(self):
        if await rpc.quickstart_possible():
            self.quickstart = quickstart_ui.create()

            def _on_done():
                self.toolbox.visible = True

            self.quickstart.on_done = lambda *_: _on_done()
            self.element.shadowRoot.append(self.quickstart.window.element)
            self.toolbox.visible = False
        else:
            self.toolbox.visible = True

    def connectedCallback(self):
        create_task_safe(self._connectedCallback_async())

    def show_window(self, title: str, component: wpc.Component):
        from wwwpy.remote.designer.ui.window_component import new_window
        w1 = new_window(title)
        w1.element.append(component.element)
        self.root_element().append(w1.element)
