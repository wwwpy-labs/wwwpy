from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from functools import cached_property
from queue import Queue
from threading import Thread
from types import FunctionType
from typing import Callable, Any

from playwright.sync_api import PageAssertions, LocatorAssertions, APIResponseAssertions, Page, sync_playwright, \
    Playwright, Browser

with sync_playwright() as pw: pass  # workaround to run playwright in a new thread. see: https://github.com/microsoft/playwright-python/issues/1685


@dataclass
class PlaywrightBunch:
    playwright: Playwright
    page: Page
    browser: Browser

    @cached_property
    def cdp(self):
        return self.page.context.new_cdp_session(self.page)


@dataclass
class PlaywrightArgs:
    url: str
    headless: bool
    queue: Queue = field(default_factory=Queue)
    instance: PlaywrightBunch | None = None


def start_playwright_in_thread(url: str, headless: bool) -> PlaywrightArgs:
    args = PlaywrightArgs(url, headless)

    def in_thread():
        start_playwright(args)
        while True:
            element = args.queue.get(timeout=30)
            if element is None:
                break
            element()

    thread = Thread(target=in_thread, daemon=True)
    thread.start()
    return args


def start_playwright(args: PlaywrightArgs) -> None:
    playwright = sync_playwright().start()
    launch_args = ['--enable-features=WebAssemblyExperimentalJSPI']
    browser = playwright.chromium.launch(headless=args.headless, args=launch_args)
    page = browser.new_page(has_touch=True)
    playwright_setup_page_logger(page)
    page.goto(args.url)
    args.instance = PlaywrightBunch(playwright, page, browser)


def playwright_setup_page_logger(page: Page):
    page.on('console', lambda msg: print(f'console [{msg.type}] ==== {msg.text}'))
    sep = '\n' + ('=' * 60) + '\n'
    page.on('pageerror', lambda exc: print(f'{sep}uncaught exception through pageerror: {sep}{exc}{sep}'))


def playwright_patch_timeout() -> None:
    import wwwpy.base_conf
    timeout_millis = wwwpy.base_conf.PLAYWRIGHT_PATCH_TIMEOUT_MILLIS
    print(f'Using PLAYWRIGHT_PATCH_TIMEOUT, current value={timeout_millis}')

    # patch playwright assertion timeout to match our configuration
    # this is temporary solution until playwright supports setting custom timeout for assertions
    # github issue: https://github.com/microsoft/playwright-python/issues/1358

    def patch_timeout(_member_obj: FunctionType) -> Callable:
        def patch_timeout_inner(*args, **kwargs) -> Any:
            __tracebackhide__ = True
            parameters = inspect.signature(_member_obj).parameters
            timeout_arg_index = list(parameters.keys()).index("timeout")
            if timeout_arg_index >= 0:
                if len(args) > timeout_arg_index:
                    args = list(args)  # type: ignore
                    args[timeout_arg_index] = timeout_millis  # type: ignore
                elif 'timeout' not in kwargs:
                    kwargs["timeout"] = timeout_millis
            return _member_obj(*args, **kwargs)

        return patch_timeout_inner

    for assertion_cls in [PageAssertions, LocatorAssertions, APIResponseAssertions]:
        for member_name, member_obj in inspect.getmembers(assertion_cls):
            if isinstance(member_obj, FunctionType):
                if "timeout" in inspect.signature(member_obj).parameters:
                    setattr(assertion_cls, member_name, patch_timeout(member_obj))
