import subprocess
from pathlib import Path

wd = Path(__file__).parent.parent.parent

# uv pip install granian
subprocess.run(['granian', '--interface', 'asgi', 'wwwpy.asgi.echo_handler:app'], cwd=wd)
