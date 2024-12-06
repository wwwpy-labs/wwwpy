import logging


async def rpctst_echo(msg: str) -> str:
    return f'echo {msg}'


async def rpctst_exec(source: str):
    """Example:
    page.mouse.click(100, 100)

    This method queue the command to be executed in the playwright thread and it neither wait the completion nor return
    the result.
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
    gl = {'page': pwb.page}
    args.queue.put(lambda: exec(source, gl))
