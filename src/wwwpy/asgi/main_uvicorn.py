import subprocess

# uv pip install 'uvicorn[standard]'
subprocess.run(['uvicorn', 'wwwpy.asgi.echo_handler:app', '--reload'])
