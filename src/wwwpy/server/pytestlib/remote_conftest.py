from js import window
import asyncio
import pytest


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
    print(f'url={url}')
    print(f'method={method}')
    print(f'data=`{data}`')
    response = await window.fetch(url, method=method, body=data)
    text = await response.text()
    return text
