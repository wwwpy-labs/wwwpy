from __future__ import annotations

import asyncio
import logging

import js

logger = logging.getLogger(__name__)


async def activate():
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


def is_active() -> bool:
    try:
        return js.window._wwwpy_dev_mode
    except AttributeError:
        return False


def _global_exception_handler(loop, context):
    # The context parameter contains details about the exception
    logger.info(f"Global handler caught: {context['message']}")
    exception = context.get('exception')
    if exception:
        logger.info(f"Exception type: {type(exception)}, Args: {exception.args}")
        logger.exception(exception)


def set_active(dev_mode: bool):
    js.window._wwwpy_dev_mode = dev_mode
