import os
from pathlib import Path


async def app(scope, receive, send):
    if scope['type'] == 'http':
        await handle_http(scope, send)
    elif scope['type'] == 'websocket':
        await handle_websocket(scope, receive, send)


async def handle_http(scope, send):
    path = scope['path']
    if path == '/':
        await serve_file('index.html', 'text/html', send)
    else:
        await send_response(200, b'Hello, world! ' + f'you requested `{path}`'.encode('utf-8'),
                            'text/plain', send)


async def handle_websocket(scope, receive, send):
    if scope['path'] != '/echo':
        return
    await send({'type': 'websocket.accept'})

    while True:
        message = await receive()
        if message['type'] == 'websocket.receive':
            text = message.get('text')
            await send({'type': 'websocket.send', 'text': f"echo -> {text}"})
        elif message['type'] == 'websocket.disconnect':
            break


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
