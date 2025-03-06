from __future__ import annotations

import logging

import pytest

from tests.common import DynSysPath
from tests.common import dyn_sys_path
from tests.common.rpc2.transport_fake import PairedTransport
from wwwpy.common.rpc2.default_skeleton import DefaultSkeleton
from wwwpy.common.rpc2.default_stub import DefaultStub
from wwwpy.common.rpc2.encoder_decoder import EncoderDecoder, JsonEncoderDecoder
from wwwpy.common.rpc2.stub import generate_stub
from wwwpy.exceptions import RemoteException

"""
This is the integration test of the parts listed below.
Beware that there are other unit tests to verify single parts of parts.

- generate_stub, it accepts the DefaultStub
- DefaultStub, which needs the Transport and the EncoderDecoder
- Skeleton
"""
logger = logging.getLogger(__name__)
# language=Python
_shared = '''
from dataclasses import dataclass

@dataclass
class Car:
    name: str
    year: int
'''
# language=Python
_called = '''
from shared import Car

def make(name:str, year: int) -> Car:
    return Car(name, year)

async def make_async(name:str, year: int) -> Car:
    import asyncio
    await asyncio.sleep(0)
    return Car(name, year)

class Dog:
    
    def bark(self, times: float) -> str:
        return ('woof ' * times).strip()
'''


class TestStubPart:
    def test_import__should_succeed(self, fixture: Fixture):
        fixture.setup_stub()
        import stub  # noqa


def test_mock_source_is_correct(fixture: Fixture):
    """This is an assumption as a base for the other tests. The written code is entirely under
    the control of the test, so it is assumed to be correct."""
    fixture.write_shared_module()
    fixture.dyn_sys_path.write_module2('called.py', _called)

    import called  # noqa
    import shared  # noqa
    assert called.make('ford', 2021) == shared.Car('ford', 2021)


def test_function_sync(fixture: Fixture):
    fixture.setup_sync()

    import stub  # noqa

    result = stub.make('Toyota', 2017)

    import shared  # noqa
    assert result == shared.Car('Toyota', 2017)


async def test_function_async(fixture: Fixture):
    fixture.setup_async()

    import stub  # noqa

    result = await stub.make_async('Toyota', 2017)

    import shared  # noqa
    assert result == shared.Car('Toyota', 2017)


def test_allowed_modules(fixture: Fixture):
    fixture.setup_skeleton(allowed_modules={})
    fixture.setup_stub()

    import stub  # noqa

    with pytest.raises(Exception):
        stub.make('Toyota', 2017)


def test_void_function(fixture: Fixture):
    fixture._server_code = 'def void_func(): pass'
    fixture.setup_sync()

    import stub  # noqa

    stub.void_func()


def test_function_exception_sync(fixture: Fixture):
    fixture._server_code = 'def raise_exception(): raise Exception("message 123")'
    fixture.setup_sync()

    import stub  # noqa

    with pytest.raises(RemoteException) as e:
        stub.raise_exception()

    assert 'message 123' in str(e)


async def test_function_exception_async(fixture: Fixture):
    fixture._server_code = 'async def raise_exception(): raise Exception("message 123")'
    fixture.setup_async()

    import stub  # noqa

    with pytest.raises(RemoteException) as e:
        await stub.raise_exception()

    assert 'message 123' in str(e)


def _make_import(obj: any) -> str:
    return f'from {obj.__module__} import {obj.__name__}'


class Fixture:
    paired_transport: PairedTransport
    encdec: EncoderDecoder

    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path
        Fixture.paired_transport = PairedTransport()
        Fixture.encdec = JsonEncoderDecoder()
        self._server_code = _called
        # Fixture.stub_transport = self.paired_transport.client
        #
        # encdec = JsonEncoderDecoder()
        # Fixture.stub_encdec = encdec
        # self.skeleton = DefaultSkeleton(self.paired_transport.server, encdec)

    def setup_skeleton(self, allowed_modules: set[str] = None):
        self.write_shared_module()
        self.dyn_sys_path.write_module2('server.py', self._server_code)

        if allowed_modules is None:
            allowed_modules = {'server'}
        skeleton = DefaultSkeleton(self.paired_transport.server, self.encdec, allowed_modules)
        self.skeleton = skeleton

    def write_shared_module(self):
        self.dyn_sys_path.write_module2('shared.py', _shared)

    def setup_stub(self):
        fixture = self
        stub_module_name = '"server"'
        stub_imports = _make_import(Fixture)
        stub_args = f'{Fixture.__name__}.paired_transport.client, {Fixture.__name__}.encdec, {stub_module_name} '
        stub = generate_stub(self._server_code, DefaultStub, stub_args)
        stub = stub_imports + '\n\n' + stub
        logger.debug(f'stub:\n{stub}')
        fixture.dyn_sys_path.write_module2('stub.py', stub)
        self.write_shared_module()

    def setup_sync(self):
        fixture = self
        fixture.setup_skeleton()
        fixture.setup_stub()

        self.paired_transport.client.send_sync_callback = lambda: self.skeleton.invoke_tobe_fixed()

    def setup_async(self):
        fixture = self
        fixture.setup_skeleton()
        fixture.setup_stub()

        async def async_callback():
            fixture.skeleton.invoke_tobe_fixed()

        fixture.paired_transport.client.send_async_callback = async_callback


@pytest.fixture
def fixture(dyn_sys_path: DynSysPath):
    dbf = Fixture(dyn_sys_path)
    yield dbf
