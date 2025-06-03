import logging
import sys
from pathlib import Path

from wwwpy.common import modlib
from wwwpy.common.designer import new_component

logger = logging.getLogger(__name__)


async def write_module_file(module: str, content: str) -> str:
    msg = f'write_module_file module={module} content len={len(content)}'
    logger.debug(msg)
    path = modlib._find_module_path(module)
    if not path:
        raise ValueError(f'Cannot find module {module}')
    path.write_text(content)
    return f'done {msg}'


def _fix_stacktrace(message: str):
    return message.replace('"/wwwpy_bundle/', '"')

async def on_exception_string(exception: str):
    exception = _fix_stacktrace(exception)
    print(exception, file=sys.stderr)

async def on_error(message: str, source: str, lineno: int, colno: int, error: str):
    print(f'rpc.on_error')
    message = _fix_stacktrace(message)
    error = _fix_stacktrace(error)
    all_str = f'message==={message}\nsource==={source}\nlineno==={lineno}\ncolno==={colno}\nerror==={error}'
    print(all_str, file=sys.stderr)


async def on_unhandledrejection(message: str):
    message = _fix_stacktrace(message)
    print(message, file=sys.stderr)


async def print_module_line(module: str, message: str, lineno: int):
    #  File "remote/designer/toolbar.py", line 140, in on_changes
    path = modlib._find_module_path(module)
    if not path:
        raise ValueError(f'Cannot find module {module}')
    print(message)
    print(_ide_path_link(path, lineno))


def _ide_path_link(path, lineno):
    ide_path_link = f'  File "{path}", line {lineno}'
    return ide_path_link


async def server_console_log(message: str):
    print(message)


async def add_new_component() -> str:
    path = new_component.add()
    if path:
        print(f'Added new component')
        print(_ide_path_link(path, 1))
        return f'Added new component file:\n\n{path.name}'
    return 'Failed to add new component'


async def quickstart_apply(quickstart_name: str) -> str:
    if not await quickstart_possible():
        return 'Quickstart not possible'
    from wwwpy.server import custom_str
    root = custom_str.get_root_folder_or_fail()
    from wwwpy.common import quickstart
    await _run_sync_in_thread(lambda: quickstart.setup_quickstart(Path(root), quickstart_name))
    logger.info(f'Quickstart applied {quickstart_name} to {root}')
    return 'Quickstart applied'


async def quickstart_possible() -> bool:
    from wwwpy.server import custom_str
    from wwwpy.common import quickstart
    root = custom_str.get_root_folder_or_fail()
    emtpy = quickstart.is_empty_project(root)
    return emtpy


import asyncio
import concurrent.futures
from typing import TypeVar, Callable

T = TypeVar('T')


async def _run_sync_in_thread(func: Callable[[], T]) -> T:
    """
    Run a synchronous function in a separate thread without blocking the event loop.

    Args:
        func: A callable that takes no arguments and returns a result of type T

    Returns:
        The result of the function execution

    Example:
        result = await run_sync_in_thread(lambda: time_consuming_sync_function(arg1, arg2))
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return await asyncio.get_event_loop().run_in_executor(executor, func)


async def server_python_version_string() -> str:
    """
    Get the Python version string from the server.
    """
    import platform
    return platform.python_version()
