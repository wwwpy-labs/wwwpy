import importlib.util
from types import ModuleType

import wwwpy

from tests import for_all_webservers
from tests.common.rpc import support3, support1, support2
from wwwpy.exceptions import RemoteException
from wwwpy.rpc import Module, RpcRequest, RpcRoute
from wwwpy.server.tcp_port import find_port
from wwwpy.unasync import unasync
from wwwpy.webserver import Webserver

support2_module_name = 'tests.common.rpc.support2'

support1_module_name = 'tests.common.rpc.support1'


# done migrating
@unasync
async def test_module_invoke_async():
    target = Module(support2)

    # THEN
    function = target['support2_concat']
    assert function.is_coroutine_function
    actual = await function.func('hello', ' world')
    assert actual == 'hello world'


# todo write the remote counterpart of the following test
# todo rewrite this so to use ast_parser and not the old Module
@for_all_webservers()
def test_rpc_integration(webserver: Webserver):
    """ server part """
    services = RpcRoute('/rpc2')

    services.allow(support3.__name__)

    webserver.set_routes(services.route)
    webserver.set_port(find_port()).start_listen().wait_ready()

    rpc_url = webserver.localhost_url() + services.route.path
    imports = 'from wwwpy.server.fetch import async_fetch_str'
    module = Module(support3)
    stub_source = wwwpy.rpc.generate_stub_source(module, rpc_url, imports)
    """ end """

    """ client part """
    client_module = _module_from_source('dynamic_module', stub_source)

    @unasync
    async def verify():
        target = await client_module.support3_mul(3, 4)
        assert target == 12

        target = await client_module.support3_concat('foo', 'bar')
        assert target == 'foobar'

        target = await client_module.support3_with_typing_import()
        assert target == {'foo': 'bar'}  # this could fail do to missing 'from typing import Dict'

        target = await client_module.support3_default_values_primitive_types(4, c=10)
        assert target == 80
        # expect errors
        exception = None
        try:
            target = await client_module.support3_throws_error('inducted exception', '')
        except RemoteException as ex:
            exception = ex
        assert exception is not None
        assert 'inducted exception' in str(exception)

        target = await client_module.support3_throws_error('', 'ok1')
        assert target == 'ok1'

    verify()
    """ end """


def _module_from_source(name: str, source: str) -> ModuleType:
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    exec(source, module.__dict__)
    return module
