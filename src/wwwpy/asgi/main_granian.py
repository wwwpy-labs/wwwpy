import subprocess

# pip install granian
subprocess.run(['granian', '--interface', 'asgi', 'wwwpy.asgi.echo_handler:app'])
