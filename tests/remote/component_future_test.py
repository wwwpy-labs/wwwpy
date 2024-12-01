from __future__ import annotations

from js import HTMLDivElement

from wwwpy.remote.component import Component, element


def test_correct_annotation():
    class Comp1(Component):
        div1: HTMLDivElement = element()

        def init_component(self):
            self.element.innerHTML = """<div data-name="div1">div1</div>"""

    c = Comp1()
    nop = c.div1
