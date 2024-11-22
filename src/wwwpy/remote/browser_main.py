from __future__ import annotations
import traceback

from inspect import iscoroutinefunction
import asyncio
import logging

import js
from js import console

import wwwpy.common.reloader as reloader
from wwwpy.common import _no_remote_infrastructure_found_text, files, _remote_module_not_found_html
from wwwpy.common.tree import print_tree
from wwwpy.remote.designer import dev_mode as dm
from wwwpy.remote.websocket import setup_websocket
from wwwpy.common.asynclib import create_task_safe

logger = logging.getLogger(__name__)


async def entry_point(dev_mode: bool = False):
    # from wwwpy.common.tree import print_tree
    # print_tree('/wwwpy_bundle')

    await setup_websocket()
    if dev_mode:
        await dm.activate()

    await _invoke_browser_main()


def _reload():
    async def reload():
        console.log('reloading')
        reloader.unload_path(files._bundle_path)
        await _invoke_browser_main()

    asyncio.create_task(reload())


async def _invoke_browser_main():
    try:
        console.log('invoke_browser_main')

        try:
            js.document.body.innerText = f'Going to import the "remote" package'
            import remote
            if hasattr(remote, 'main'):
                if iscoroutinefunction(remote.main):
                    await remote.main()
                else:
                    remote.main()
        except ModuleNotFoundError as e:
            js.document.body.innerHTML = _remote_module_not_found_html
        except Exception as e:
            _show_exception(e, _no_remote_infrastructure_found_text)
            from wwwpy.server.designer import rpc
            create_task_safe(rpc.on_exception_string(traceback.format_exc()))
    finally:
        if dm.is_active():
            from wwwpy.remote.designer.ui import dev_mode_component
            dev_mode_component.show()


def _show_exception(e, html: str):
    js.document.body.innerHTML = html
    js.document.body.insertAdjacentHTML('beforeend', '<br><br>')

    exc_trace = traceback.format_exc()
    exc_str = 'Exception: ' + str(e) + '\n\n' + exc_trace + '\n\n'
    pre = js.document.createElement('pre')
    pre.innerText = exc_str
    js.document.body.appendChild(pre)
