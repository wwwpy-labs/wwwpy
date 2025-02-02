import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

from echo_handler import app

# uv pip install hypercorn
asyncio.run(serve(app, Config()))
