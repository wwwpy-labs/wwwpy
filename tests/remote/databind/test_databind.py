"""this should test only InputTargetAdapter directly, not the whole databind"""
from __future__ import annotations
import logging
from dataclasses import dataclass

import js
import pytest
from js import document

from tests.server.rpc4tests import rpctst_exec
from wwwpy.common.databind.databind import Binding
from wwwpy.remote.databind.bind_wrapper import InputTargetAdapter

logger = logging.getLogger(__name__)


@dataclass
class User:
    name: str


@dataclass
class Car:
    color: str


async def test_databind_input_string1(fixture: Fixture):
    # GIVEN
    tag1 = _new_target_adapter()
    user = User('foo1')

    # WHEN
    _bind(user, 'name', tag1)

    # THEN
    assert tag1.input.value == 'foo1'


async def test_databind_input_string2(fixture: Fixture):
    # GIVEN
    tag1 = _new_target_adapter()
    car1 = Car('yellow')

    # WHEN
    _bind(car1, 'color', tag1)

    # THEN
    assert tag1.input.value == 'yellow'


async def test_databind_input_string__target_to_source(fixture: Fixture):
    # GIVEN
    tag1 = _new_target_adapter()
    car1 = Car('')

    # WHEN
    _bind(car1, 'color', tag1)

    await rpctst_exec("page.locator('#tag1').press_sequentially('yellow1')")

    # THEN
    assert car1.color == 'yellow1'


def _new_target_adapter(tag_id: str = 'tag1'):
    tag1: js.HTMLInputElement = document.createElement('input')  # noqa
    tag1.id = tag_id
    document.body.append(tag1)
    return InputTargetAdapter(tag1)


def _bind(instance, attr_name, target_adapter):
    target = Binding(instance, attr_name, target_adapter)
    target.apply_binding()


class Fixture:
    pass


@pytest.fixture
def fixture():
    document.body.innerHTML = ''
    return Fixture()
