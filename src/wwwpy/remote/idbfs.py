import asyncio
import logging
from pathlib import Path

import js
from pyodide.ffi import create_proxy, to_js
from wwwpy.common.asynclib import create_task_safe

logger = logging.getLogger(__name__)


async def _fs_idbfs_sync(n):
    queue = asyncio.Queue(1)
    js.pyodide.FS.syncfs(n, create_proxy(lambda err: queue.put_nowait(err)))
    res = await asyncio.wait_for(queue.get(), 5)
    logger.debug(f'fs_idbfs_sync({n}) res: {res}')
    return res


def fs_idbfs_load(): return create_task_safe(_fs_idbfs_sync(1))


def fs_idbfs_save(): return create_task_safe(_fs_idbfs_sync(0))


async def fs_idbfs_mount(mount_point: str):
    if Path(mount_point).exists():
        return logger.warning('already mounted')
    js.pyodide.FS.mkdirTree(mount_point)
    js.pyodide.FS.mount(js.pyodide.FS.filesystems.IDBFS, to_js({}), mount_point)
    await fs_idbfs_load()
