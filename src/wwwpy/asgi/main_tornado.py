import subprocess

# uv pip install tornado

import tornado.ioloop
import tornado.web
import tornado_asgi_handler
import echo_handler

application = tornado.web.Application([
    (r".*", tornado_asgi_handler.ASGIHandler, dict(asgi_app=echo_handler.app))
])
application.listen(8000)

try:
    tornado.ioloop.IOLoop.current().start()
except KeyboardInterrupt as err:
    print("Server stopped")
