from __future__ import annotations

import asyncio
import logging
import traceback
from inspect import iscoroutinefunction

import js
from js import console

import wwwpy.common.reloader as reloader
from wwwpy.common import _no_remote_infrastructure_found_text, files, _remote_module_not_found_html
from wwwpy.common.asynclib import create_task_safe
from wwwpy.remote.designer import dev_mode as dm
from wwwpy.remote.websocket import setup_websocket

logger = logging.getLogger(__name__)


async def entry_point(dev_mode: bool = False):
    # from wwwpy.common.tree import print_tree
    # print_tree('/wwwpy_bundle')
    import wwwpy
    console.log(wwwpy.__banner__)
    await setup_websocket()
    await dm.set_active(dev_mode)
    await _invoke_browser_main()


def _reload():
    async def reload():
        console.log('reloading')
        # for p in Path(files._bundle_path).iterdir():
        #     if p.name == 'wwwpy':
        #         continue
        #     reloader.unload_path(str(p))
        reloader.unload_path(files._bundle_path, skip_wwwpy=True)
        await _invoke_browser_main()

    asyncio.create_task(reload())


async def _invoke_browser_main():
    try:
        console.log('invoke_browser_main')

        try:
            js.document.documentElement.innerHTML = ''
            js.document.head.innerHTML = ''
            for attr in js.document.documentElement.attributes:
                js.document.documentElement.removeAttributeNode(attr)

            js.document.body.innerText = f'Importing the "remote" package...'
            import remote
            if hasattr(remote, 'main'):
                if iscoroutinefunction(remote.main):
                    await remote.main()
                else:
                    remote.main()
        except Exception as e:
            explain_text = _no_remote_infrastructure_found_text
            if isinstance(e, ModuleNotFoundError) and e.name == 'remote':
                explain_text = _remote_module_not_found_html
            js.console.error(f'Exception: {e}')
            _show_exception(e, explain_text)
            from wwwpy.server.designer import rpc
            create_task_safe(rpc.on_exception_string(traceback.format_exc()))
    finally:
        dm.on_after_remote_main()


def _reset_document():
    pass
    # the following code is very controversial.
    # js.document.open()
    # js.document.write('<!DOCTYPE html><html></html>')
    # js.document.close()


def _show_exception(e, html: str):
    js.document.body.innerHTML = html
    js.document.body.insertAdjacentHTML('beforeend', '<br><br>')

    exc_trace = traceback.format_exc()
    exc_str = 'Exception: ' + str(e) + '\n\n' + exc_trace + '\n\n'
    pre = js.document.createElement('pre')
    pre.innerText = exc_str
    js.document.body.appendChild(pre)
