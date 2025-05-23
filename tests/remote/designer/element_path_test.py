import js
from js import document

import wwwpy.remote.component as wpc
from tests.common import dyn_sys_path
from wwwpy.common.designer.html_locator import Node
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.element_path import locator_from


def test_target_path_to_component(tmp_path, dyn_sys_path):
    # GIVEN
    dyn_sys_path.write_module('', 'component1.py', '''import js

import wwwpy.remote.component as wpc


class Component1(wpc.Component):
    btn1: js.HTMLButtonElement = wpc.element()

    def connectedCallback(self):
        self.element.innerHTML = """
        <div></div>
        <div class='class1'>foo
            <button data-name='btn1' id='btn1id'>bar</button>
        </div>
    """
    ''')

    from component1 import Component1  # noqa
    component1 = Component1()

    document.body.innerHTML = ''
    document.body.appendChild(component1.element)

    target = document.querySelector("#btn1id")
    assert target

    # WHEN
    actual = locator_from(target)

    # THEN
    path = [Node("div", 1, {'class': 'class1'}),
            Node("button", 0, {'data-name': 'btn1', 'id': 'btn1id'})]

    assert actual.class_module == 'component1'
    assert actual.class_name == 'Component1'
    assert actual.path == path


def test_target_path__without_component():
    # GIVEN

    document.body.innerHTML = """
        <div></div>
        <div class='class1'>foo
            <button data-name='btn1' id='btn1id'>bar</button>
        </div>
    """

    target = document.querySelector("#btn1id")
    assert target

    # WHEN
    actual = locator_from(target)

    # THEN
    assert actual is None


def test_target_path__unattached_piece_of_dom():
    # GIVEN
    document.body.innerHTML = ''
    div = document.createElement("div")
    div.setAttribute('attr1', 'foo')
    div.innerHTML = """
        <div></div>
        <div class='class1'>foo
            <button data-name='btn1' id='btn1id'>bar</button>
        </div>
    """

    target = div.querySelector("#btn1id")
    assert target

    # WHEN
    actual = locator_from(target)

    # THEN
    assert actual is None


async def test_component_with_shadow_root():
    # GIVEN (one component with shadow root)
    # we don't need two
    class ShadowWpc(wpc.Component):
        div1: js.HTMLElement = wpc.element()

        def init_component(self):
            self.element.attachShadow(dict_to_js({'mode': 'open'}))
            self.element.shadowRoot.innerHTML = """<br><div data-name="div1">shadow</div>"""

    shadow_wpc = ShadowWpc()
    document.body.append(shadow_wpc.element)

    # WHEN
    actual = locator_from(shadow_wpc.div1)

    # THEN
    expected_path = [Node("div", 1, {'data-name': 'div1'})]
    assert actual is not None
    assert actual.class_module == __name__  # this file itself
    assert actual.class_name == 'ShadowWpc'
    assert actual.path == expected_path, f'actual.path=```\n{actual.path}\n``` != ```\n{expected_path}\n```'


class TestSlottedComponent:
    def _gen_classes(self):
        # we need to generate the classes dynamically be sure we override the registered custom element tag_name
        # other tests should do the same
        class SlottedWpc(wpc.Component, tag_name='slotted-wpc'):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        class RootWpc(wpc.Component):
            inner: js.HTMLElement = wpc.element()

            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = \
                    """<br><slotted-wpc data-name="slotted1"><div data-name="inner">inner-div</div></slotted-wpc>"""

        return RootWpc, SlottedWpc

    async def test_class_name(self):
        # GIVEN
        RootWpc, SlottedWpc = self._gen_classes()

        root_wpc = RootWpc()
        document.body.append(root_wpc.element)

        # WHEN
        actual = locator_from(root_wpc.inner)

        # THEN
        assert actual is not None

        assert actual.class_module == __name__  # it is the current module itself
        assert actual.class_name != 'SlottedWpc'
        assert actual.class_name == 'RootWpc'

    async def test_path(self):
        # GIVEN
        RootWpc, SlottedWpc = self._gen_classes()

        root_wpc = RootWpc()
        document.body.append(root_wpc.element)

        # WHEN
        actual = locator_from(root_wpc.inner)

        # THEN
        expected_path = [
            Node('slotted-wpc', 1, {'data-name': 'slotted1'}),
            Node("div", 0, {'data-name': 'inner'})]

        assert actual is not None
        assert actual.path == expected_path, f'actual.path=```\n{actual.path}\n``` != ```\n{expected_path}\n```'
