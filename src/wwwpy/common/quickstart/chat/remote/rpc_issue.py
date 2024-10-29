import js
import wwwpy.remote.component as wpc

class RpcIssueAlert(wpc.Component):
    button1: js.HTMLButtonElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<h2>Server.rpc issue:
The package server.rpc is not completely supported by the hot-reload yet.
It is necessary to refresh the browser. <br>
<a href='https://github.com/wwwpy-labs/wwwpy/issues/6' target='_blank'>See and vote the github issue</a>
<br>
<button data-name="button1" style='transform: scale(2.0,2.0); margin: 2em 4em'>Refresh page</button>
</h2>

        """
        self.element.style.position = 'absolute'
        self.element.style.top = '0'
        self.element.style.display = 'none'
        self.element.style.backgroundColor = 'red'
        try:
            from server import rpc
        except ImportError as e:
            self.element.style.display = 'block'

    async def button1__click(self, event):
        js.console.log('handler button1__click event =', event)
        js.location.reload()
    
