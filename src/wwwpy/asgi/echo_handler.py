import json
import os
from pathlib import Path
import asyncio

import logging

logging.getLogger().setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logging.warning('Watch out!')  # will print a message to the console
logging.info('I told you so')


async def app(scope, receive, send):
    scope_type = scope['type']
    if scope_type == 'http':
        await handle_http(scope, send)
    elif scope_type == 'websocket':
        await handle_websocket(scope, receive, send)
    else:
        logger.info(f"scope_type: {scope_type}")


async def handle_http(scope, send):
    path = scope['path']
    logger.info(f"http path: {path}")
    if path == '/':
        await serve_file('index.html', 'text/html', send)
    else:
        await send_response(200, b'Hello, world! ' + f'you requested `{path}`'.encode('utf-8'),
                            'text/plain', send)


async def handle_websocket(scope, receive, send):
    # scope_str = json.dumps(scope, indent=2)
    logger.info(f"websocket scope: {scope}")
    scope_path = scope['path']
    if scope_path != '/echo':
        return
    await send({'type': 'websocket.accept'})

    # Start background task to send 'hello' every 3 seconds
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
