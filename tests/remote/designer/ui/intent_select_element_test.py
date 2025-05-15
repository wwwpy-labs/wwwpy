import js

import wwwpy.remote.component as wpc
from tests.remote.rpc4tests_helper import rpctst_exec
from wwwpy.common.designer.canvas_selection import CanvasSelection
from wwwpy.common.exitlib import on_exit
from wwwpy.common.injectorlib import injector
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.ui.intent_manager import IntentManager
from wwwpy.remote.designer.ui.intent_select_element import SelectElementIntent


class Comp1(wpc.Component):
    div1: js.HTMLDivElement = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """<div data-name="div1" id="div1">I'm div1</div>"""


async def test_click__set_the_canvas_selection():
    on_exit(injector._clear)
    canvas_selection = CanvasSelection()
    injector.bind(canvas_selection)

    intent_manager = IntentManager()
    intent_manager.install()
    on_exit(intent_manager.uninstall)

    target = SelectElementIntent()
    intent_manager.current_selection = target

    c1 = Comp1()

    js.document.body.appendChild(c1.element)
    assert canvas_selection.current_selection is None

    # WHEN
    await rpctst_exec("page.locator('#div1').click()")

    # THEN
    canvas_selection = canvas_selection.current_selection
    assert canvas_selection is not None
    assert canvas_selection.class_name == Comp1.__name__

# todo test
#  hover, should move the SelectionIndicatorFloater to the target
#  click on 'designer' element, should not select the target and keep the selected_intent (maybe this goes in intent_manager_test.py)
