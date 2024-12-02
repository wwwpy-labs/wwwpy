from __future__ import annotations

import sys
from pathlib import Path
from time import sleep

from playwright.sync_api import Page, expect

from tests import for_all_webservers
from tests.common import restore_sys_path
from tests.server.page_fixture import PageFixture, fixture
from wwwpy.bootstrap import bootstrap_routes
from wwwpy.common.rpc.custom_loader import CustomFinder
from wwwpy.resources import library_resources
from wwwpy.server.conv import convention
from wwwpy.webserver import Webserver
from wwwpy.websocket import WebsocketPool, PoolEvent, Change

file_parent = Path(__file__).parent
layer_5_rpc_server = file_parent / 'layer_5_support/rpc_server'


class TestServerRpc:

    @for_all_webservers()
    def test_rpc(self, fixture: PageFixture):
        fixture.set_path(layer_5_rpc_server)
        fixture.start_remote()

        expect(fixture.page.locator('body')).to_have_text('42')

    @for_all_webservers()
    def test_rpc_issue_double_load(self, fixture: PageFixture):
        # related to the stubber to being loaded twice
        fixture.set_path(layer_5_rpc_server)
        fixture.start_remote()

        expect(fixture.page.locator('body')).to_have_text('42')

        fixture.page.goto(fixture.webserver.localhost_url())
        expect(fixture.page.locator('body')).to_have_text('42')


class TestWebsocketRoute:

    @for_all_webservers()
    def test_server_to_remote_message(self, page: Page, webserver: Webserver):
        # language=python
        python_code = """

from js import document, WebSocket
document.body.innerHTML = ''

def log(msg):
    document.body.innerHTML += f'|{msg}'

es = WebSocket.new(f'ws://127.0.0.1:$(webserver.port)/ws')
es.onopen = lambda e: log('open')
es.onmessage = lambda e: log(f'message:{e.data}')        
        """

        python_code = python_code.replace('$(webserver.port)', str(webserver.port))
        webserver.set_http_route(*bootstrap_routes(resources=[library_resources()], python=python_code))
        ws_pool = WebsocketPool('/ws')
        webserver.set_http_route(ws_pool.http_route).start_listen()

        page.goto(webserver.localhost_url())

        expect(page.locator('body')).to_have_text('|open')
        [sleep(0.1) for _ in range(100) if len(ws_pool.clients) == 0]
        assert len(ws_pool.clients) == 1
        client = ws_pool.clients[0]
        client.send('42')
        expect(page.locator('body')).to_have_text('|open|message:42')
        client.send('11')
        expect(page.locator('body')).to_have_text('|open|message:42|message:11')

    @for_all_webservers()
    def test_pool_change(self, page: Page, webserver: Webserver):
        # language=python
        python_code = """

from js import document, WebSocket
document.body.innerHTML = ''
def log(msg):
    document.body.innerHTML += f'|{msg}'

es = WebSocket.new(f'ws://127.0.0.1:$(webserver.port)/ws')

def message(msg):
    log(f'message:{msg}')
    es.close()
    
es.onopen = lambda e: log('open')
es.onmessage = lambda e: message(e.data)        
                """

        python_code = python_code.replace('$(webserver.port)', str(webserver.port))
        webserver.set_http_route(*bootstrap_routes(resources=[library_resources()], python=python_code))

        changes = []

        ws_pool = WebsocketPool('/ws')
        ws_pool.on_before_change.append(lambda event: changes.append(event.change))
        webserver.set_http_route(ws_pool.http_route).start_listen()

        page.goto(webserver.localhost_url())

        expect(page.locator('body')).to_have_text('|open')
        assert changes == [Change.add]
        [sleep(0.1) for _ in range(100) if len(ws_pool.clients) == 0]
        assert len(ws_pool.clients) == 1
        client = ws_pool.clients[0]
        client.send('close')
        expect(page.locator('body')).to_have_text('|open|message:close')
        assert changes == [Change.add, Change.remove]

    @for_all_webservers()
    def test_remote_to_server_message(self, page: Page, webserver: Webserver):
        # language=python
        python_code = """
from js import WebSocket
es = WebSocket.new(f'ws://127.0.0.1:$(webserver.port)/ws')    
es.onopen = lambda e: [es.send('foo1'), es.close()]
                """

        python_code = python_code.replace('$(webserver.port)', str(webserver.port))
        webserver.set_http_route(*bootstrap_routes(resources=[library_resources()], python=python_code))
        incoming_messages = []

        def before_change(change: PoolEvent):
            if change.add:
                change.endpoint.listeners.append(lambda msg: incoming_messages.append(msg))

        ws_pool = WebsocketPool('/ws')
        ws_pool.on_before_change.append(before_change)
        webserver.set_http_route(ws_pool.http_route).start_listen()

        page.goto(webserver.localhost_url())

        [sleep(0.1) for _ in range(100) if len(incoming_messages) != 2]
        assert len(incoming_messages) == 2
        assert incoming_messages == ['foo1', None]


class _RemoteConnections:
    def __init__(self, websocket_pool):
        self.ws_pool = websocket_pool
        self.changes = []
        websocket_pool.on_before_change.append(lambda event: self.changes.append(event.change))

    def wait_for_connection(self):
        retry_assert_eq(lambda: self.changes, lambda: [Change.add])
        self.changes.clear()


class TestRpcRemote:
    layer_5_rpc_remote = file_parent / 'layer_5_support/rpc_remote'

    def test_remote_rpc_interceptor(self, restore_sys_path):
        """Importing remote.rpc should not raise an exception even from the server side
        even though it imports 'js' that does not exist on the server side.
        It is because the import process of such package is handled and modified"""

        sys.path.insert(0, str(self.layer_5_rpc_remote))
        sys.meta_path.insert(0, CustomFinder({'remote', 'remote.rpc'}))
        import remote
        assert remote
        import remote.rpc
        assert remote.rpc

    @for_all_webservers()
    def test_rpc_remote(self, page: Page, webserver: Webserver, restore_sys_path):
        project = convention(self.layer_5_rpc_remote, webserver)
        webserver.start_listen()

        remote_connections = _RemoteConnections(project.websocket_pool)

        page.goto(webserver.localhost_url())
        expect(page.locator('body')).to_have_text('ready')

        remote_connections.wait_for_connection()

        # because convention imported layer_5_rpc_remote in sys.path we can import the following
        from remote.rpc import Layer5Rpc1
        client = remote_connections.ws_pool.clients[0]
        client.rpc(Layer5Rpc1).set_body_inner_html('server-side')

        expect(page.locator('body')).to_have_text('server-side')

    @for_all_webservers()
    def test_websocket_recover(self, page: Page, webserver: Webserver, restore_sys_path):
        project = convention(self.layer_5_rpc_remote, webserver)
        webserver.start_listen()

        remote_connections = _RemoteConnections(project.websocket_pool)

        page.goto(webserver.localhost_url())
        expect(page.locator('body')).to_have_text('ready')

        remote_connections.wait_for_connection()

        client = remote_connections.ws_pool.clients[0]
        client.send(None)  # this will disconnect the client

        retry_assert_eq(lambda: remote_connections.changes, lambda: [Change.remove, Change.add])

        # because convention imported layer_5_rpc_remote in sys.path we can import the following
        from remote.rpc import Layer5Rpc1
        client = remote_connections.ws_pool.clients[0]
        client.rpc(Layer5Rpc1).set_body_inner_html('server-side')

        expect(page.locator('body')).to_have_text('server-side')


def retry_assert_eq(a, b):
    [sleep(0.1) for _ in range(50) if a() != b()]
    assert a() == b()
