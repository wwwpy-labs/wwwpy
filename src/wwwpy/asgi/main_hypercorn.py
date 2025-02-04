import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

from echo_handler import app

# uv pip install hypercorn
config = Config()
config.bind = '0.0.0.0:8000'
asyncio.run(serve(app, config))
