import asyncio
import logging
from pathlib import Path

logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.info('Loading module')


def open_browser_once():
    open_browser_once.__code__ = (lambda: None).__code__
    import webbrowser
    webbrowser.open('http://localhost:8000')


# scope # https://github.com/django/asgiref/blob/main/asgiref/typing.py#L66
async def app(scope, receive, send):
    func = _scopes.get(scope['type'], None)
    if func:
        await func(scope, receive, send)
    else:
        logger.info(f"scope type not handled: {scope['type']}")


async def scope_lifespan(scope, receive, send):
    open_browser_once()
    logger.info(f"lifespan scope: {scope}")
    await send({'type': 'lifespan.startup.complete'})

    message = await receive()
    if message['type'] == 'lifespan.shutdown':
        await send({'type': 'lifespan.shutdown.complete'})


async def scope_http(scope, receive, send):
    path = scope['path']
    headers = dict(scope['headers'])
    logger.info(f"http path: {path}")
    if path == '/':
        await serve_file('index.html', 'text/html', send)
    elif path == '/favicon.ico':  # png actually
        await serve_file('favicon.png', 'image/png', send)
    elif path == '/post':
        body = await _all_body(receive)
        await send_response(200, body, 'text/plain', send)
    else:
        await send_response(200, b'Hello, world! ' + f'you requested `{path}`'.encode('utf-8'),
                            'text/plain', send)


async def scope_websocket(scope, receive, send):
    logger.info(f"websocket scope: {scope}")
    scope_path = scope['path']
    headers = dict(scope['headers'])
    if scope_path != '/echo':
        return
    await send({'type': 'websocket.accept'})
    send_text = lambda t: send({'type': 'websocket.send', 'text': t})

    async def send_hello():
        try:
            await send_text('producing hello messages every 2 seconds')
            hello_count = 0
            while True:
                hello_count += 1
                await asyncio.gather(send_text(f'hello {hello_count}'), asyncio.sleep(2))
        except asyncio.CancelledError:
            pass

    hello_task = asyncio.create_task(send_hello())

    try:
        while True:
            message = await receive()
            if message['type'] == 'websocket.receive':
                await send_text(f"echo -> {message.get('text')}")
            elif message['type'] == 'websocket.disconnect':
                break
    finally:
        # Cancel the background task when the connection is closed
        hello_task.cancel()


async def serve_file(filename, content_type, send):
    try:
        content = (Path(__file__).parent / filename).read_bytes()
        await send_response(200, content, content_type, send)
    except FileNotFoundError:
        await send_response(404, b'File not found', 'text/plain', send)


async def send_response(status, body, content_type, send):
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [[b'content-type', content_type.encode()], ],
    })
    await send({'type': 'http.response.body', 'body': body, })


_scopes = {
    'http': scope_http,
    'websocket': scope_websocket,
    'lifespan': scope_lifespan,
}


async def _all_body(receive):
    body = b""
    more_body = True

    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body
