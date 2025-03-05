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
    fixture.dyn_sys_path.write_module2('shared.py', _shared)
    fixture.dyn_sys_path.write_module2('called.py', _called)

    import called  # noqa
    import shared  # noqa
    assert called.make('ford', 2021) == shared.Car('ford', 2021)


def test_function_sync(fixture: Fixture):
    fixture.setup_skeleton()
    fixture.setup_stub()

    import stub  # noqa

    result = stub.make('Toyota', 2017)

    import shared  # noqa
    assert result == shared.Car('Toyota', 2017)


def _make_import(obj: any) -> str:
    return f'from {obj.__module__} import {obj.__name__}'


class Fixture:
    paired_transport: PairedTransport
    encdec: EncoderDecoder

    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path
        Fixture.paired_transport = PairedTransport()
        Fixture.encdec = JsonEncoderDecoder()
        # Fixture.stub_transport = self.paired_transport.client
        #
        # encdec = JsonEncoderDecoder()
        # Fixture.stub_encdec = encdec
        # self.skeleton = DefaultSkeleton(self.paired_transport.server, encdec)

    def setup_skeleton(self):
        self.dyn_sys_path.write_module2('shared.py', _shared)
        self.dyn_sys_path.write_module2('server.py', _called)

        skeleton = DefaultSkeleton(self.paired_transport.server, self.encdec)

        self.paired_transport.client.send_sync_callback = lambda: skeleton.invoke_sync()

    def setup_stub(self):
        fixture = self
        stub_module_name = '"server"'
        stub_imports = _make_import(Fixture)
        stub_args = f'{Fixture.__name__}.paired_transport.client, {Fixture.__name__}.encdec, {stub_module_name} '
        stub = generate_stub(_called, DefaultStub, stub_args)
        stub = stub_imports + '\n\n' + stub
        logger.debug(f'stub:\n{stub}')
        fixture.dyn_sys_path.write_module2('stub.py', stub)
        fixture.dyn_sys_path.write_module2('shared.py', _shared)


@pytest.fixture
def fixture(dyn_sys_path: DynSysPath):
    dbf = Fixture(dyn_sys_path)
    yield dbf
