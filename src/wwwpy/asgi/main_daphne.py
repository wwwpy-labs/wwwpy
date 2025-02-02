import subprocess

# uv pip install daphne
subprocess.run(['daphne', 'wwwpy.asgi.echo_handler:app'])
