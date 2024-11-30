import asyncio
import logging
from pathlib import Path

logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.info('Loading module')


async def app(scope, receive, send):
    scope_type = scope['type']
    if scope_type == 'http':  # https://github.com/django/asgiref/blob/main/asgiref/typing.py#L66
        await handle_http(scope, send)
    elif scope_type == 'websocket':
        await handle_websocket(scope, receive, send)
    else:
        logger.info(f"scope_type not handled: {scope_type}")


async def handle_http(scope, send):
    path = scope['path']
    logger.info(f"http path: {path}")
    if path == '/':
        await serve_file('index.html', 'text/html', send)
    else:
        await send_response(200, b'Hello, world! ' + f'you requested `{path}`'.encode('utf-8'),
                            'text/plain', send)


async def handle_websocket(scope, receive, send):
    logger.info(f"websocket scope: {scope}")
    scope_path = scope['path']
    if scope_path != '/echo':
        return
    await send({'type': 'websocket.accept'})

    async def send_hello():
        try:
            hello_count = 0
            while True:
                hello_count += 1
                await send({'type': 'websocket.send', 'text': f'hello {hello_count}'})
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            pass

    hello_task = asyncio.create_task(send_hello())

    try:
        while True:
            message = await receive()
            if message['type'] == 'websocket.receive':
                text = message.get('text')
                await send({'type': 'websocket.send', 'text': f"echo -> {text}"})
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
