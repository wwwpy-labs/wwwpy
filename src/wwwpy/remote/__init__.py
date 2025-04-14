from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# PUBLIC-API
def dict_to_js(o):
    import js
    import pyodide
    return pyodide.ffi.to_js(o, dict_converter=js.Object.fromEntries)


async def micropip_install(package):
    from js import pyodide
    await pyodide.loadPackage('micropip')
    import micropip
    await micropip.install([package])


# def set_timeout(callback: Callable[[], Union[None, Awaitable[None]]], timeout_millis: int | None = 0):
#     from pyodide.ffi import create_once_callable
#     from js import window
#     window.setTimeout(create_once_callable(callback), timeout_millis)


def dict_to_py(js_obj):
    import js
    py_dict = {}
    # Iterate through properties, including those in the prototype chain
    current = js_obj
    while current:
        for prop in js.Object.getOwnPropertyNames(current):
            try:
                value = getattr(js_obj, prop)
                if not callable(value):  # Skip methods
                    _ = str(value)  # some properties throw errors when accessed
                    py_dict[prop] = value
            except Exception as ex:
                try:
                    logger.warning(f'Error accessing property `{prop}` of {current}: {ex}')
                except:
                    pass
        current = js.Object.getPrototypeOf(current)

    return py_dict
