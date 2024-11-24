from __future__ import annotations

import asyncio
import logging

import js

logger = logging.getLogger(__name__)

_wwwpy_dev_mode = 'wwwpy_dev_mode'


async def activate():
    setattr(js.window, _wwwpy_dev_mode, True)
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
    return hasattr(js.window, _wwwpy_dev_mode)


def _global_exception_handler(loop, context):
    # The context parameter contains details about the exception
    logger.info(f"Global handler caught: {context['message']}")
    exception = context.get('exception')
    if exception:
        logger.info(f"Exception type: {type(exception)}, Args: {exception.args}")
        logger.exception(exception)
