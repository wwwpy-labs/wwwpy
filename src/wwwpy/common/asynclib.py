import asyncio
from typing import Union, Coroutine, Any

# todo evaluate if best to use Awaitable instead of Coroutine
OptionalCoroutine = Union[None, Coroutine[Any, Any, None]]
_task_set = set()


def create_task_safe(coro):
    """Create an asyncio task and keep a reference to prevent garbage collection.

    See https://stackoverflow.com/questions/71938799/python-asyncio-create-task-really-need-to-keep-a-reference
    """
    task = asyncio.create_task(coro)
    _task_set.add(task)
    task.add_done_callback(_task_set.discard)
    return task
