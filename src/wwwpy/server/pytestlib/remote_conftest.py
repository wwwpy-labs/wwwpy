import asyncio

import pytest
from js import window

from wwwpy.common.fetch_debug import fetch_debug


@pytest.fixture(scope="session")
def event_loop():
    # this prevents pytest-asyncio to closing the pyodide event loop (webloop)
    yield asyncio.get_running_loop()


def pytest_sessionstart(session):
    print(f'invocation_dir={session.config.invocation_dir}')
    print(f'rootpath={session.config.rootpath}')


def pytest_xvirt_send_event(event_json):
    async def callback():
        path = '#xvirt_notify_path_marker#'
        await async_fetch_str(path, method='POST', data=event_json)

    asyncio.create_task(callback())


async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    print(__name__ + ' ' + fetch_debug(url, method, data))
    response = await window.fetch(url, method=method, body=data)
    text = await response.text()
    return text


def pytest_runtest_setup(item):
    _clean_doc_now()


# intent_manager_tests.py fails without the following, don't know why
def pytest_runtest_teardown(item, nextitem):
    _clean_doc_now()


def _clean_doc_now():
    from wwwpy.remote import remote_fixtures
    remote_fixtures.clean_document_now()
