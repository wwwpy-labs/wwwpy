import asyncio
import logging

from tests.timeouts import timeout_multiplier

logger = logging.getLogger(__name__)


async def rpctst_echo(msg: str) -> str:
    return f'echo {msg}'


async def rpctst_exec(source: str, timeout_secs: int = 1) -> None:
    """Example:
    page.mouse.click(100, 100)
    page.locator('input').fill('foo1')

    This method queue the command to be executed in the playwright thread,
    it waits the completion but do not return the result.
    """
    from wwwpy.server.pytestlib.xvirt_impl import xvirt_instances
    from wwwpy.server.pytestlib.playwrightlib import PlaywrightBunch
    i = len(xvirt_instances)
    assert i == 1, f'len(xvirt_instances)={i}'
    xvirt = xvirt_instances[0]
    args = xvirt.playwright_args
    assert args is not None
    pwb: PlaywrightBunch = args.instance
    assert pwb is not None
    gl = {'page': pwb.page, 'pwb': pwb}
    loop = asyncio.get_running_loop()
    done = asyncio.Event()
    ex = []

    def _execute():
        try:
            exec(source, gl)
        except Exception as e:
            logger.error(f'Error executing source: {e}')
            ex.append(e)
        loop.call_soon_threadsafe(done.set)

    args.queue.put(_execute)
    timeout = timeout_secs * timeout_multiplier()
    try:
        await asyncio.wait_for(done.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(f"Execution timed out after {timeout} seconds for code `{source}`")

    if ex: raise ex[0]
