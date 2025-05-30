from __future__ import annotations

import asyncio
import logging
import random
from typing import TypeVar, Any, Type, TypeGuard, Callable, overload

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


class AnimationFrameTracker:
    """Tracks animation frames and calls a callback."""

    def __init__(self, callback):
        self._callback = callback
        self._raf_id = None
        self._on_animation_frame = create_proxy(self._on_animation_frame)

    def start(self):
        if self._raf_id is None:
            self._raf_id = js.window.requestAnimationFrame(self._on_animation_frame)

    def stop(self):
        if self._raf_id is not None:
            js.window.cancelAnimationFrame(self._raf_id)
            self._raf_id = None

    def _on_animation_frame(self, timestamp):
        if self._raf_id is None:
            return

        self._raf_id = js.window.requestAnimationFrame(self._on_animation_frame)
        self._callback(timestamp)

    @property
    def is_tracking(self):
        return self._raf_id is not None


_instanceof: Callable[[..., ...], bool] = js.eval('(i,t) => i instanceof t')

T = TypeVar('T')


def is_instance_of(instance: Any, js_type: Type[T]) -> TypeGuard[T]:
    """Check if the instance is of the given JavaScript type.
    Example: is_instance_of(js.document, js.HTMLDocument) will return True.
    """
    return _instanceof(instance, js_type)


@overload
def is_contained(target: js.Element, container: js.Element):
    """Check if target is a descendant of container, including shadow DOM and slots."""


@overload
def is_contained(target: js.Element, is_container: Callable[[js.Element], bool]):
    """the second argument will be called with all the pertinent nodes in the DOM tree;
    if it returns True, the target is considered contained."""


def is_contained(target, container):
    """Determines if target is a descendant of container, accounting for shadow DOM and slots."""
    if target is None:
        raise ValueError(f'target is None')
    if container is None:
        raise ValueError(f'container is None')
    if callable(container):
        is_container = container
        logger.debug(f'target: `{_pretty(target)}` container: `lambda...`')
    else:
        is_container = lambda x: x == container
        logger.debug(f'target: `{_pretty(target)}` container: `{_pretty(container)}`')
    node = target
    while node:
        if hasattr(node, 'tagName') and is_container(node):
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


def get_deepest_element(x, y) -> js.Element | None:
    """
    Get the deepest ele at the event coordinates by recursively traversing shadow DOMs.
    """

    def _rec(root):
        ele = root.elementFromPoint(x, y)
        ele_shadow = _shadow_root_of(ele)
        if root == ele_shadow:
            return root.host

        if ele and ele_shadow:
            rec = _rec(ele_shadow)
            if rec:
                return rec

        return ele

    return _rec(js.document)


def _shadow_root_of(element) -> js.ShadowRoot | None:
    if element is None:
        return None

    if hasattr(element, 'shadowRoot') and element.shadowRoot and is_instance_of(element.shadowRoot, js.ShadowRoot):
        return element.shadowRoot
    return None


def _pretty(node: js.Element):
    if hasattr(node, 'tagName'):
        identifier = node.dataset.name if node.hasAttribute('data-name') else node.id
        return f'{node.tagName.lower()}#{identifier}.{node.className}[{node.innerHTML.strip()[:20]}…]'
    return str(node)


def closest_across_shadow(el, selector):
    current = el
    while current:
        match = current.closest(selector)
        if match:
            return match
        root = current.getRootNode()
        if not is_instance_of(root, js.ShadowRoot):
            return None
        current = root.host
