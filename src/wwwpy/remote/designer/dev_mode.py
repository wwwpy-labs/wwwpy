from __future__ import annotations

import asyncio
import logging

import js

from wwwpy.common.injectorlib import injector
from wwwpy.remote.designer.ui.element_selector import ElementSelector

logger = logging.getLogger(__name__)


async def set_active(dev_mode: bool):
    js.window._wwwpy_dev_mode = dev_mode
    if dev_mode:
        await _activate()


def is_active() -> bool:
    try:
        return js.window._wwwpy_dev_mode
    except AttributeError:
        return False


async def _activate():
    from wwwpy.remote import micropip_install
    from wwwpy.common import designer

    for package in designer.pypi_packages:
        await micropip_install(package)

    from wwwpy.remote.designer import helpers
    js.window.onerror = helpers._on_error
    js.window.onunhandledrejection = helpers._on_unhandledrejection
    from wwwpy.remote.designer import log_redirect
    log_redirect.redirect_logging()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_global_exception_handler)

    # dependency injection
    injector._clear()

    from wwwpy.common.eventbus import EventBus
    injector.bind(EventBus())  # todo, maybe use a named binding so we use our own event bus
    from wwwpy.remote.designer.ui.intent_manager import IntentManager
    intent_manager = IntentManager()
    intent_manager.install()
    injector.bind(intent_manager)
    injector.bind(ElementSelector())
    from wwwpy.common.designer.canvas_selection import CanvasSelection
    injector.bind(CanvasSelection())
    from wwwpy.remote.designer import di_remote
    di_remote.register_bindings()


def on_after_remote_main():
    if not is_active():
        return
    from wwwpy.remote.designer.ui import dev_mode_component
    dev_mode_component.show()  # todo it looks like it can take ~ 1s or more; investigate,
    # maybe micropip installing rope has to do with it


def _global_exception_handler(loop, context):
    # The context parameter contains details about the exception
    if 'message' in context:
        logger.info(f"Global handler caught: {context['message']}")
    if 'exception' not in context:
        logger.error(f"Global handler caught: {context}")
        return
    exception = context.get('exception')
    if exception:
        logger.info(f"Exception type: {type(exception)}, Args: {exception.args}")
        logger.exception(exception)
