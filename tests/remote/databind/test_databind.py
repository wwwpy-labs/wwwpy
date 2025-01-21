import logging
from dataclasses import dataclass

import js
from js import document
from pyodide.ffi import create_proxy

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


async def test_databind_input_string1():
    # GIVEN
    tag1 = _new_docu_input_tag1()

    user = User('foo1')

    # WHEN
    target = Binding(user, 'name', InputTargetAdapter(tag1))
    target.apply_binding()

    # THEN
    assert tag1.value == 'foo1'


async def test_databind_input_string2():
    # GIVEN
    tag1 = _new_docu_input_tag1()

    car1 = Car('yellow')

    # WHEN
    target = Binding(car1, 'color', InputTargetAdapter(tag1))
    target.apply_binding()

    # THEN
    assert tag1.value == 'yellow'


async def test_databind_input_string__target_to_source():
    # GIVEN
    tag1 = _new_docu_input_tag1()

    car1 = Car('')

    # WHEN
    target = Binding(car1, 'color', InputTargetAdapter(tag1))
    target.apply_binding()

    await rpctst_exec("page.locator('#tag1').press_sequentially('yellow1')")

    # THEN
    assert car1.color == 'yellow1'


def _new_docu_input_tag1():
    document.body.innerHTML = '<input id="tag1">'
    tag1: js.HTMLInputElement = document.getElementById('tag1')  # noqa
    return tag1
