# Seamless communication server/remote

wwwpy allows you to call server-side functions from the browser seamlessly, 
without the need to write API endpoints.
You can also do the reverse, calling functions in the browser(s) from the server just as easily.


## Server-side functions


By convention all the functions defined in module `server/rpc.py` are available to be called from the browser.
See the quickstart project `upload` for an [example](../src/wwwpy/common/quickstart/upload/server/rpc.py) .

You can also specify a return value, which will be sent back to the browser.

General rules:
- Specify type hints for the function arguments and return value.
- The functions that start with an underscore `_` are not exposed to the browser.

```python
# server/rpc.py
async def add(a: int, b: int) -> int:
    return a + b
```

You can define and use both async and synchronous functions. 
Note that async functions are more performant 
because they do not block the browser's main thread. 

### Calling server-side functions from the browser
```python
# remote/component1.py

class Component1(wpc.Component):
    # [...]
    async def button1__click(self):
        result = await rpc.add(1, 2)
        js.alert(f'The result is {result}')
        
```


## Browser-side functions

By convention all the functions defined in module `remote/rpc.py` are available to be called from the server.
See the quickstart project `chat` for an [example](../src/wwwpy/common/quickstart/chat/remote/rpc.py) .

You _cannot_ specify a return value for these functions and they _must_ be defined as not async.


General rules:
- Define a class. `Rpc` is just a convention, you can name it as you wish. 
- Specify type hints for the method arguments.
- The functions that start with an underscore `_` are not exposed to the browser.


```python
# remote/rpc.py

class Rpc:
    def show_alert(self, message: str):
        import js
        js.alert(message)
```


### Calling browser-side functions from the server

The following code is an example of how to call a browser-side function from the server.
This is a tricky example because it calls all the connected clients from inside a server-side function.

  
```python
from wwwpy.server.configure import websocket_pool
from remote import rpc

async def send_alert_to_all(message: str) -> str:
    for client in websocket_pool.clients:
        client.rpc(rpc.Rpc).show_alert(message)
    return 'done'
```

There is the plan to handle server code and scheduled server events (that work with hot-reload): see this [issue](https://github.com/wwwpy-labs/wwwpy/issues/7).