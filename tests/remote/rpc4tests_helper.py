from __future__ import annotations

from typing import TYPE_CHECKING

from wwwpy.server import rpc4tests

if TYPE_CHECKING:
    from playwright.sync_api import Page  # noqa


async def rpctst_exec(source: str | list[str], timeout_secs: int = 1) -> None:
    if isinstance(source, str):
        await rpc4tests.rpctst_exec(source, timeout_secs)
    elif isinstance(source, list):
        for cmd in source:
            await rpc4tests.rpctst_exec(cmd, timeout_secs)
    else:
        raise TypeError(f"source must be str or list[str], got {type(source)}")

# class PlaywrightPageCallable(Protocol):
#     def __call__(self, page: Page) -> None: ...

# PlaywrightPageCallable = Callable[[Page], None]

# def page_exec(block: Callable[[Page], None]):
#     pass

# def main():
#     page_exec(lambda page: page.mouse.click(0, 0))
#     page_exec(lambda page: page.mouse.click(0, 0))
#
#     def test_func(page: Page):
#         page.mouse.click(0, 0)

#     page_exec(test_func)
#
# if __name__ == '__main__':
#     main()
