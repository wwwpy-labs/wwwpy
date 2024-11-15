import asyncio

_active_tasks = set()

def create_task_safe(coro):
    """Create an asyncio task and keep a reference to prevent garbage collection.

    See https://stackoverflow.com/questions/71938799/python-asyncio-create-task-really-need-to-keep-a-reference
    """
    task = asyncio.create_task(coro)
    _active_tasks.add(task)
    task.add_done_callback(_active_tasks.discard)
    return task