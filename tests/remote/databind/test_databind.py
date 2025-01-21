import inspect
import inspect
import logging
from asyncio import sleep
from dataclasses import dataclass

import js
from js import document
from pyodide.ffi import create_proxy

from tests.server.rpc4tests import rpctst_exec
from wwwpy.common.databind.databind import new_dataclass_binding

logger = logging.getLogger(__name__)


async def test_databind_input_string1():
    # GIVEN
    document.body.innerHTML = '<input id="tag1">'
    tag1: js.HTMLInputElement = document.getElementById('tag1')  # noqa

    @dataclass
    class User:
        name: str

    user = User('foo1')

    # WHEN
    target = new_dataclass_binding(user, 'name', tag1)
    target.apply_binding()

    # THEN
    assert tag1.value == 'foo1'


async def test_databind_input_string2():
    # GIVEN
    document.body.innerHTML = '<input id="tag1">'
    tag1: js.HTMLInputElement = document.getElementById('tag1')  # noqa

    @dataclass
    class Car:
        color: str

    car1 = Car('yellow')

    # WHEN
    target = new_dataclass_binding(car1, 'color', tag1)
    target.apply_binding()

    # THEN
    assert tag1.value == 'yellow'


async def test_databind_input_string__target_to_source():
    # GIVEN
    document.body.innerHTML = '<input id="tag1">'
    tag1: js.HTMLInputElement = document.getElementById('tag1')  # noqa

    @dataclass
    class Car:
        color: str

    car1 = Car('')

    # WHEN
    target = new_dataclass_binding(car1, 'color', tag1)
    target.apply_binding()

    # PRODUCTION CODE!
    tag1.addEventListener('input', create_proxy(lambda event: setattr(car1, 'color', tag1.value)))
    ################

    await rpctst_exec("page.locator('#tag1').press_sequentially('yellow1')")

    # THEN
    assert car1.color == 'yellow1'
