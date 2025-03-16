import logging

import js
from js import document

import wwwpy.remote.component as wpc
from wwwpy.server.rpc4tests import rpctst_exec

logger = logging.getLogger(__name__)


async def test_some():
    class Comp1(wpc.Component):
        button1: js.HTMLButtonElement = wpc.element()

        def init_component(self):
            self.element.innerHTML = """<button data-name="button1" style='height: 200px; width: 200px'></button>"""
            self.events = []

        def button1__click(self, event):
            self.events.append(event)
            self.button1.innerHTML += '.'

    comp1 = Comp1()
    document.body.innerHTML = ''
    document.body.append(comp1.element)
    for idx in range(1, 15):
        await rpctst_exec('page.mouse.click(100, 100)')
        assert len(comp1.events) == idx
        assert len(comp1.button1.innerHTML) == idx
        # await _assert_retry(lambda: len(comp1.events) == idx)
        # await _assert_retry(lambda: len(comp1.button1.innerHTML) == idx)


# async def _assert_retry(condition):
#     source = inspect.getsource(condition).strip()
#     __tracebackhide__ = True
#     [await sleep(0.01) for _ in range(100) if not condition()]
#     assert condition(), f'wait_condition timeout `{source}`'
