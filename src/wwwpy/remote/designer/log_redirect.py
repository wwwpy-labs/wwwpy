import asyncio

from js import console
from wwwpy.common.designer import log_emit
from wwwpy.server.designer import rpc

_log_buffer = asyncio.Queue()


async def _process_buffer():
    """This technique avoids the issue of wrong log order"""
    while True:
        msg = await _log_buffer.get()
        await rpc.server_console_log(msg)


def redirect_logging():
    asyncio.create_task(_process_buffer())

    def emit(msg: str):
        console.log(msg)
        # this is not correct because we are not in a coroutine
        # but it probably works because we are in the browser with just one event loop
        _log_buffer.put_nowait(msg)

    log_emit.add_once(emit)
    log_emit.warning_to_log()
