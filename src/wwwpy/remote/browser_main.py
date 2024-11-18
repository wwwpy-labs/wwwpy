from __future__ import annotations

from inspect import iscoroutinefunction
import asyncio
from logging import exception

import js
from js import console

import wwwpy.common.reloader as reloader
from wwwpy.common import _no_remote_infrastructure_found_text, files
from wwwpy.common.tree import print_tree
from wwwpy.remote.designer import dev_mode as dm
from wwwpy.remote.websocket import setup_websocket


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
        except Exception as e:
            import traceback
            msg = _no_remote_infrastructure_found_text + ' Exception: ' + str(
                e) + '\n\n' + traceback.format_exc() + '\n\n'
            pre = js.document.createElement('pre')
            pre.innerText = msg
            js.document.body.innerHTML = ''
            js.document.body.appendChild(pre)
            return

    finally:
        if dm.is_active():
            from wwwpy.remote.designer.ui import dev_mode_component
            dev_mode_component.show()
