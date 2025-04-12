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


_instanceof = js.eval('(i,t) => i instanceof t')


def is_instance_of(instance, js_type):
    """Check if the instance is of the given JavaScript type.
    Example: is_instance_of(js.document, js.HTMLDocument) will return True.
    """
    return _instanceof(instance, js_type)


def is_contained(target, container):
    """Determines if target is a descendant of container, accounting for shadow DOM and slots."""
    if target is None:
        raise ValueError(f'target is None')
    if container is None:
        raise ValueError(f'container is None')
    logger.debug(f'target: `{_pretty(target)}` container: `{_pretty(container)}`')
    node = target
    while node:
        if node == container:
            return True

        # Check if node is assigned to a slot
        if hasattr(node, "assignedSlot") and node.assignedSlot:
            node = node.assignedSlot
            logger.debug(f'assignedSlot: {_pretty(node)}')
            continue

        # If in a shadow tree (i.e., root has a host), move to the host element.
        if is_instance_of(node, js.ShadowRoot):
            node = node.host
            logger.debug(f'host: {_pretty(node)}')
        else:
            # Otherwise, move up in the light DOM.
            if not hasattr(node, 'parentNode'):
                # logger.debug(f'node has no parentNode: {_pretty(node)}')
                # break
                raise ValueError(f'node has no parentNode: {_pretty(node)}')
            node = node.parentNode
            logger.debug(f'parentNode: {_pretty(node)}')

    return False


def _pretty(node):
    if hasattr(node, 'tagName'):
        return f'{node.tagName.lower()}#{node.id}.{node.className}[{node.outerHTML.strip()[:20]}…]'
    return f'_pretty({node})'
