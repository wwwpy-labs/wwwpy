import asyncio

import js
from js import document
from pyodide.ffi import create_proxy


async def script_load_once(src: str, type=None):
    # logger.debug(f'load {src}')
    src_short = src.split('/')[-1]
    scripts = list(filter(lambda s: s.src == src, document.head.querySelectorAll('script')))  # noqa
    scripts: list[js.HTMLScriptElement]
    script = None if not scripts else scripts[0]

    if script:
        # logger.debug(f'  found script with same src: {src_short} type={script.type}')
        assert script.type == type
    else:
        # logger.debug(f'  load is needed, no script with same src found: {src_short}')
        script = document.createElement('script')
        script.src = src
        if type:
            script.type = type
        script.__async_event = asyncio.Event()
        script.onload = create_proxy(lambda e: script.__async_event.set())
        document.head.append(script)

    # logger.debug(f'  waiting for script to load: {src_short}')
    await script.__async_event.wait()
    # logger.debug(f'  event set: {src_short}')
