from js import window
from pyodide.ffi import create_once_callable


def pytest_xvirt_notify(event):
    print('siamo arrivati qui')

    async def callback():
        path = '#xvirt_notify_path_marker#'
        await async_fetch_str(path, method='POST', data=event.to_json())

    set_timeout(callback)


async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    print(f'url={url}')
    print(f'method={method}')
    print(f'data=`{data}`')
    response = await window.fetch(url, method=method, body=data)
    text = await response.text()
    return text


def set_timeout(callback, timeout=0):
    window.setTimeout(create_once_callable(callback), timeout)