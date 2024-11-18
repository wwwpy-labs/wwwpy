from __future__ import annotations

import js

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

def is_active() -> bool:
    return hasattr(js.window, _wwwpy_dev_mode)
