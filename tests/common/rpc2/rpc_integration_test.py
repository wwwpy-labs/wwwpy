from __future__ import annotations

import logging

import pytest

from tests.common import DynSysPath
from tests.common import dyn_sys_path
from wwwpy.common.rpc2.encoder_decoder import json_encoder_decoder_def
from wwwpy.common.rpc2.stub_generator import generate_stub, DefaultStub
from wwwpy.common.rpc2.transport import Transport

"""
This is the integration test of the parts listed below.
Beware that there are other unit tests to verify single parts of parts.

- generate_stub, it accepts the DefaultStub
- DefaultStub, which needs the Transport and the EncoderDecoder
- Skeleton
"""
logger = logging.getLogger(__name__)
_shared = '''
from dataclasses import dataclass

@dataclass
class Car:
    name: str
    year: int
'''
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
        # generate stub
        stub_imports = _make_import(Fixture) + '\n' + _make_import(json_encoder_decoder_def)
        stub_args = f'{Fixture.__name__}.transport_fake, json_encoder_decoder_def()'
        stub = generate_stub(_called, DefaultStub, stub_args)
        stub = stub_imports + '\n\n' + stub
        logger.debug(f'stub:\n{stub}')
        fixture.dyn_sys_path.write_module2('stub.py', stub)
        fixture.dyn_sys_path.write_module2('shared.py', _shared)

        import stub  # noqa


def test_mock_source_is_correct(fixture: Fixture):
    """This is an assumption as a base for the other tests. The written code is entirely under
    the control of the test, so it is assumed to be correct."""
    fixture.dyn_sys_path.write_module2('shared.py', _shared)
    fixture.dyn_sys_path.write_module2('called.py', _called)

    import called  # noqa
    import shared  # noqa
    assert called.make('ford', 2021) == shared.Car('ford', 2021)


def _make_import(obj: any) -> str:
    return f'from {obj.__module__} import {obj.__name__}'


class TransportFake(Transport):
    pass


class Fixture:
    transport_fake: TransportFake

    def __init__(self, dyn_sys_path: DynSysPath):
        self.dyn_sys_path = dyn_sys_path
        Fixture.transport_fake = TransportFake()


@pytest.fixture
def fixture(dyn_sys_path: DynSysPath):
    dbf = Fixture(dyn_sys_path)
    yield dbf
