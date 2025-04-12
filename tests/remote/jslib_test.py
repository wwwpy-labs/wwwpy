import logging

import js

import wwwpy.remote.component as wpc
from tests.remote.remote_fixtures import clean_document
from wwwpy.remote import dict_to_js
from wwwpy.remote.jslib import is_contained

logger = logging.getLogger(__name__)


class Test_is_descendant_of_container():

    async def test_simple_contained(self, clean_document):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        outer = js.document.getElementById('outer')
        inner = js.document.getElementById('inner')
        assert is_contained(inner, outer)

    async def test_container_itself(self, clean_document):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        outer = js.document.getElementById('outer')
        assert is_contained(outer, outer)

    async def test_not_contained(self, clean_document):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        outer = js.document.getElementById('outer')
        other = js.document.getElementById('other')
        assert not is_contained(other, outer)

    async def test_reproduce_issue_20250412(self, clean_document):
        class SlottedComponent(wpc.Component, tag_name='slotted-component'):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        class CompRoot(wpc.Component):
            slotted1: SlottedComponent = wpc.element()
            inner: js.HTMLElement = wpc.element()

            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slotted-component data-name="slotted1"><span><div data-name="inner"></div></span></slotted-component>'

        root = CompRoot()
        js.document.body.append(root.element)

        slotted1 = root.slotted1.element
        inner = root.inner
        assert is_contained(inner, slotted1)

    async def test_with_shadow_on_outer(self, clean_document):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        outer = js.document.getElementById('outer')
        shadow = outer.attachShadow(dict_to_js({'mode': 'open'}))
        shadow.innerHTML = '<div id="shadow"></div>'
        shadow_div = shadow.getElementById('shadow')
        assert is_contained(shadow_div, outer)

    async def test_with_shadow_on_inner(self, clean_document):
        js.document.body.innerHTML = """<div id="outer"><div id="inner"></div></div><div id="other"></div>"""
        outer = js.document.getElementById('outer')
        inner = js.document.getElementById('inner')
        shadow = inner.attachShadow(dict_to_js({'mode': 'open'}))
        shadow.innerHTML = '<div id="shadow"></div>'
        shadow_div = shadow.getElementById('shadow')
        assert is_contained(shadow_div, inner)

    async def test_with_slots(self, clean_document):
        class Comp1(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        inner_list = []

        class Comp11(wpc.Component):
            inner: js.HTMLElement = wpc.element()

            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<div data-name="inner"></div>'
                inner_list.append(self.inner)

        snippet = Comp1.component_metadata.build_snippet({'id': 'outer'}, Comp11.component_metadata.html_snippet)
        logger.debug(f'snippet: `{snippet}`')
        js.document.body.innerHTML = snippet
        outer = js.document.getElementById('outer')
        assert len(inner_list) == 1
        inner = inner_list[0]
        assert is_contained(inner, outer)

    async def test_with_slots_triple(self, clean_document):
        class Comp0(wpc.Component):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<slot></slot>'

        js.document.body.innerHTML = Comp0.component_metadata.build_snippet({},
                                                                            "<span id='outer'><div id='inner'></div></span>")
        outer = js.document.getElementById('outer')
        inner = js.document.getElementById('inner')
        assert is_contained(inner, outer)
