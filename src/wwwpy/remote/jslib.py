import asyncio
import logging
import random

import js
from js import document
from pyodide.ffi import create_once_callable
from pyodide.ffi import create_proxy

logger = logging.getLogger(__name__)


# logger.setLevel('DEBUG')


async def script_load_once(src: str, script_type='', **kwargs) -> bool:
    """This function loads a (javascript) script once. It waits for the script to load and returns True if the script was loaded,
    and False if the script was already loaded."""

    marker = f'm-{random.randint(1000, 9999)}'
    logger.debug(f'{marker} script_load_once: {src} {script_type} {kwargs}')

    scripts = list(filter(lambda s: s.src == src, document.head.querySelectorAll('script')))  # noqa
    scripts: list[js.HTMLScriptElement]
    need_load = not scripts
    script = None if need_load else scripts[0]

    if script:
        logger.debug(f'{marker}   found script with same src: {src} type={script.type}')
        assert script.type == script_type, f'script.type=`{script.type}`, script_type=`{script_type}`'
    else:
        logger.debug(f'{marker}  load is needed, no script with same src found: {src}')
        script = document.createElement('script')
        # copy all kwargs to the script
        for key, value in kwargs.items():
            setattr(script, key, value)
        script.src = src
        if script_type:
            script.type = script_type
        script.__async_event = asyncio.Event()
        script.onload = create_proxy(lambda e: script.__async_event.set())
        document.head.append(script)

    logger.debug(f'{marker}  waiting for script to load: {src}')
    await script.__async_event.wait()
    logger.debug(f'{marker}  event set: need_load={need_load} {src}')
    return need_load


async def waitAnimationFrame():
    event = asyncio.Event()
    js.window.requestAnimationFrame(create_once_callable(lambda *_: event.set()))
    await event.wait()


def is_descendant_of_container(target, container):
    node = target
    while node:
        if node == container:
            return True
        # Attempt to retrieve the root node (to check if we're in a shadow DOM)
        root = node.getRootNode() if hasattr(node, "getRootNode") else None
        # If in a shadow tree (i.e., root has a host), move to the host element.
        if root is not None and hasattr(root, "host"):
            node = root.host
        else:
            # Otherwise, move up in the light DOM.
            node = node.parentNode
    return False
