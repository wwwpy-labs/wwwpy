import asyncio
import logging
import weakref

import js
import pytest
from js import document, HTMLElement, Event, HTMLDivElement

from wwwpy.remote import dict_to_js
from wwwpy.remote.component import Component, attribute, element, get_component, from_element

logger = logging.getLogger(__name__)


def test_component_metadata():
    class Comp1(Component, tag_name='comp-1'): ...

    assert Comp1.component_metadata.clazz == Comp1
    assert 'comp' in Comp1.component_metadata.tag_name


def test_simple_html():
    class Comp1(Component):
        def init_component(self):
            self.element.innerHTML = '<div>hello</div>'
            # beware of https://stackoverflow.com/questions/43836886/failed-to-construct-customelement-error-when-javascript-file-is-placed-in-head !!

    comp1 = Comp1()
    assert 'hello' in comp1.element.innerHTML


def test_define_custom_metadata():
    class Comp1(Component, tag_name='tag-1'): ...

    assert Comp1.component_metadata.clazz == Comp1
    assert Comp1.component_metadata.tag_name == 'tag-1'
    assert Comp1.component_metadata.html_snippet == '<tag-1 ></tag-1>'
    assert Comp1.component_metadata.registered


def test_metadata_build_snippet():
    class Comp1(Component, tag_name='tag-1'): ...

    metadata = Comp1.component_metadata
    assert metadata.build_snippet() == '<tag-1 ></tag-1>'
    assert metadata.build_snippet({'data-name': 'foo'}) == '<tag-1 data-name="foo"></tag-1>'
    assert metadata.build_snippet({'data-name': 'foo'}, 'hello') == '<tag-1 data-name="foo">hello</tag-1>'


def test_define_custom_metadata__auto_define_False():
    class Comp1(Component, tag_name='tag-1', auto_define=False): ...

    assert not Comp1.component_metadata.registered


def test_no_custom_metadata__auto_define_True():
    class Comp1(Component): ...

    assert Comp1.component_metadata.registered


def test_document_tag_creation():
    class Comp2(Component):

        def init_component(self):
            self.element.attachShadow(dict_to_js({'mode': 'open'}))
            self.element.shadowRoot.innerHTML = '<h1>hello123</h1>'

    ele = document.createElement(Comp2.component_metadata.tag_name)
    assert 'hello123' in ele.shadowRoot.innerHTML


def test_when_shadow__elements_should_be_looked_on_it():
    class Comp1(Component):
        foo1: HTMLElement = element()

        def init_component(self):
            self.element.attachShadow(dict_to_js({'mode': 'open'}))
            self.element.shadowRoot.innerHTML = '<div data-name="foo1">yes</div>'

    comp1 = Comp1()
    assert 'yes' in comp1.foo1.innerHTML


def test_append_tag_to_document():
    class Comp2(Component):

        def connectedCallback(self):
            self.element.innerHTML = '<h1>hello456</h1>'

    document.body.innerHTML = Comp2.component_metadata.html_snippet
    assert 'hello456' in document.body.innerHTML


def test_redefining_an_element_should_be_ok():
    class Comp10a(Component, tag_name='comp-10'):
        pass

    class Comp10b(Component, tag_name='comp-10'):
        pass


class TestAfterInit:
    async def test_after_init_async(self):
        actual = []
        event = asyncio.Event()

        class Comp1(Component):
            def init_component(self):
                self.element.innerHTML = '<div>hello</div>'
                actual.append(1)

            async def after_init_component(self):
                actual.append(2)
                event.set()

        comp1 = Comp1()
        # wait for 5 secs max
        await asyncio.wait_for(event.wait(), timeout=5)
        assert actual == [1, 2]

    def test_after_init_sync(self):
        actual = []

        class Comp1(Component):
            def init_component(self):
                self.element.innerHTML = '<div>hello</div>'
                actual.append(1)

            def after_init_component(self):
                actual.append(2)

        comp1 = Comp1()
        assert actual == [1, 2]


class TestElement:

    def test_HTMLElement_attribute_not_found_should_raise(self):
        class Comp5(Component):
            div1: HTMLElement = element()
            foo1: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<div data-name="div1">789</div>'

        comp = Comp5()
        assert comp.div1.innerHTML == '789'

        try:
            comp.element_not_found_raises = True
            foo1 = comp.foo1
            assert False, 'Should raise AttributeError'
        except AttributeError:
            pass

    def test_component_element_that_do_not_exist__should_not_raise(self):
        class Comp5a(Component): ...

        class Comp5b(Component):
            foo1: Comp5a = element()

        comp = Comp5b()

    def test_Component_attribute(self):
        class Comp6(Component, tag_name='comp-6'):
            div1: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<div data-name="div1">abc</div>'

        class Comp7(Component):
            c6: Comp6 = element()

            def init_component(self):
                self.element.innerHTML = '<comp-6 data-name="c6"></comp-6>'

        comp7 = Comp7()
        assert comp7.c6.div1.innerHTML == 'abc'

    def TODO_test_component_declared_as_js_element(self):
        # TODO it needs the right technique to see if the HTML type is ok
        # the behaviour of the current _find_python_attribute/_check_type is reliable
        # but as soon as we change the implementation, the reload start to give errors
        class Comp1(Component, tag_name='comp-1'):
            div1: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<div data-name="div1">abc</div>'

        class Comp2(Component):
            c1: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<comp-1 data-name="c1"></comp-1>'

        comp2 = Comp2()
        assert not isinstance(comp2.c1, Component)
        assert 'abc' in comp2.c1.innerHTML

    def test_wrong_component_type(self):
        class CompUnused(Component):
            ...

        class CompWrongType(Component):
            c6: CompUnused = element()  # this is actually a Comp6!

            def init_component(self):
                self.element.innerHTML = '<comp-6 data-name="c6"></comp-6>'

        try:
            comp = CompWrongType()
            nop = comp.c6
            assert False, 'Should raise a TypeError'
        except TypeError:
            import traceback
            traceback.print_exc()

    def TODO_test_wrong_element_type(self):
        # TODO it needs the right technique to see if the HTML type is ok
        # the code below is very erratic.
        # js_ok = js.eval("(e,ann) => e instanceof ann")(ele, ann)

        class Comp1(Component):
            br: HTMLDivElement = element()

            def init_component(self):
                self.element.innerHTML = '<br data-name="br">'

        try:
            comp = Comp1()
            nop = comp.br
            assert False, 'Should raise a TypeError'
        except TypeError:
            import traceback
            traceback.print_exc()

    def test_sub_element_type(self):
        class Comp1(Component):
            br: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<br data-name="br">'

        comp = Comp1()
        nop = comp.br

    def test_define_new_root(self):
        class Comp8(Component):
            root: HTMLElement
            div1: HTMLElement = element()

            def root_element(self):
                return self.root

            def init_component(self):
                self.root = document.createElement('div')
                self.root.innerHTML = '<div data-name="div1">root</div>'

        comp = Comp8()
        assert comp.div1.innerHTML == 'root'

    def test_caching(self):
        """This ensures that when we access once an attribute, it is cached; we test it
        removing the element and reading it again, if it is cached, it should be the same instance (and not
        throw an exception)
        """

        class Comp1(Component):
            div1: HTMLElement = element(cached=True)

            def init_component(self):
                self.element.innerHTML = '<div data-name="div1">abc</div>'

        comp = Comp1()
        div1 = comp.div1
        div1.remove()

        assert div1 == comp.div1

    def test_cached_False(self):
        """This ensures that when we access once an attribute, it is cached; we test it
        removing the element and reading it again, if it is cached, it should be the same instance (and not
        throw an exception)
        """

        class Comp1(Component):
            div1: HTMLElement = element()

            def init_component(self):
                self.element.innerHTML = '<div data-name="div1">abc</div>'

        comp = Comp1()
        div1 = comp.div1
        div1.remove()

        assert comp.div1 is None


class TestElementEventBinding:

    def test_simple_bind(self):
        actual = []

        class Comp1(Component):
            def init_component(self):
                self.element.innerHTML = "<button data-name='foo'>foo</button>"

            def foo__click(self, *args):
                actual.append(1)

        target = Comp1()
        foo = target.element.querySelector(f'[data-name="foo"]')
        foo.click()
        assert [1] == actual

    def test_underscore_in_event_is_seen_as_dash(self):
        actual = []

        class Comp1(Component):
            def init_component(self):
                self.element.innerHTML = "<button data-name='foo'>foo</button>"

            def foo__custom_1(self, *args):
                actual.append(1)

        target = Comp1()
        foo = target.element.querySelector(f'[data-name="foo"]')
        foo.dispatchEvent(Event.new('custom-1'))
        assert [1] == actual

    def test_on_sub_component__issue20240923(self):
        events = []

        class CChild(Component):
            def init_component(self):
                self.element.innerHTML = "<div>hello</div>"

        class CParent(Component):
            def init_component(self):
                self.element.innerHTML = CChild.component_metadata.build_snippet({'data-name': 'foo'})

            def foo__click(self, event):
                events.append(1)

        target = CParent()
        foo = target.element.querySelector(f'[data-name="foo"]')
        foo.click()

        assert [1] == events

    def test_on_sub_component_with_ComponentDeclaration__issue20240923(self):
        events = []

        class CChild(Component):
            def init_component(self):
                self.element.innerHTML = "<div>hello</div>"

        class CParent(Component):
            foo: CChild = element()  # component declaration

            def init_component(self):
                self.element.innerHTML = CChild.component_metadata.build_snippet({'data-name': 'foo'})

            def foo__click(self, event):
                events.append(1)

        target = CParent()
        foo = target.element.querySelector(f'[data-name="foo"]')
        foo.click()

        assert [1] == events


class TestAttributes:

    def test_verify_value(self):
        class Comp1(Component):
            text: str = attribute()

        comp = Comp1()
        comp.text = 'abc'
        assert 'abc' == comp.text
        assert 'abc' == comp.element.getAttribute('text')

    def test_observed_attributes__with_default_metadata(self):
        calls = []

        class Comp3(Component):
            text = attribute()

            def attributeChangedCallback(self, name, oldValue, newValue):
                calls.append((name, oldValue, newValue))

        comp = Comp3()
        comp.text = 'abc'

        assert calls == [('text', None, 'abc')]
        calls.clear()

        comp.element.setAttribute('text', 'def')
        assert calls == [('text', 'abc', 'def')]

    def test_observed_attributes__with_custom_metadata(self):
        calls = []

        class Comp4(Component, tag_name='comp-4'):
            text = attribute()

            def attributeChangedCallback(self, name, oldValue, newValue):
                calls.append((name, oldValue, newValue))

        comp = Comp4()
        comp.text = 'abc'

        assert calls == [('text', None, 'abc')]
        calls.clear()

        comp.element.setAttribute('text', 'def')
        assert calls == [('text', 'abc', 'def')]

    def test_redefined_element_should_be_ok(self):
        class Comp9a(Component, tag_name='comp-9'):
            attr1 = attribute()

            def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
                self.element.innerHTML = f'Comp9a'

        comp = document.createElement('comp-9')
        comp.setAttribute('attr1', 'x')
        assert 'Comp9a' == comp.innerHTML

        class Comp9b(Component, tag_name='comp-9'):
            attr1 = attribute()

            def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
                self.element.innerHTML = f'Comp9b'

        comp = document.createElement('comp-9')
        comp.setAttribute('attr1', 'x')
        assert 'Comp9b' == comp.innerHTML

    def test_custom_name(self):
        class Comp1(Component):
            class_: str = attribute(name='class')

        comp = Comp1()

        comp.element.setAttribute('class', 'some-class')

        assert 'some-class' == comp.class_

    def test_custom_name__should_be_used_for_observed(self):
        calls = []

        class Comp1(Component):
            class_: str = attribute(name='class')

            def attributeChangedCallback(self, name, oldValue, newValue):
                calls.append((name, oldValue, newValue))

        comp = Comp1()
        comp.class_ = 'abc'

        assert calls == [('class', None, 'abc')]
        calls.clear()

        comp.element.setAttribute('class', 'def')
        assert calls == [('class', 'abc', 'def')]

    def test_set_none_should_remove(self):
        class Comp1(Component):
            attr1: str | None = attribute()

        comp = Comp1()
        comp.attr1 = 'abc'
        comp.attr1 = None
        assert comp.element.hasAttribute('attr1') is False


class Test_InitComponent_that_throws:
    def test_should_call_after_init_anyway(self):
        class Comp1(Component):
            def init_component(self):
                raise Exception('testing error')

            def after_init_component(self):
                self.element.innerHTML = '<div>hello</div>'

        comp = Comp1()
        assert 'hello' in comp.element.innerHTML


class TestGetComponent:
    def test_get_component__should_not_return_none(self):
        class Comp1(Component):
            def init_component(self):
                raise Exception('testing error')

        comp = Comp1()
        assert get_component(comp.element) is comp

    def test_correctly_typed(self):
        class Comp1(Component): ...

        c = Comp1()
        assert get_component(c.element, Comp1) is c

    def test_incorrect_component(self):
        class Comp1(Component): ...

        class Comp2(Component): ...

        with pytest.raises(TypeError):
            get_component(Comp1().element, Comp2)

    def test_not_even_a_component(self):
        class Comp1(Component): ...

        class NotAComponent: ...

        with pytest.raises(TypeError):
            get_component(Comp1().element, NotAComponent)


class TestInheritance:
    def test_inheritance_no_tag_name(self):
        class Comp1(Component):
            def some_method(self):
                return 1

        class Comp2(Comp1):
            def init_component(self):
                self.element.innerHTML = '<div>hello</div>'

        c2 = Comp2()
        assert c2.some_method() == 1
        assert 'hello' in c2.element.innerHTML

    def test_inheritance_no_tag_name__use_generated(self):
        class Comp1(Component):
            def some_method(self):
                return 1

        class Comp2(Comp1):
            def init_component(self):
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<div>hello</div>'

        js.document.body.innerHTML = Comp2.component_metadata.html_snippet
        logger.debug(f'innerHTML: {js.document.body.innerHTML}')
        element = js.document.body.firstElementChild
        c2 = get_component(element, Comp2)

        assert c2.some_method() == 1

    async def test_inheritance_with_explicit_tag_name(self):
        class Comp1(Component, auto_define=False):
            def some_method(self):
                return 1

        class Comp2(Comp1, tag_name='comp-test_inheritance_with_explicit_tag_name'):
            def init_component(self):
                logger.debug(f'init_component')
                self.element.attachShadow(dict_to_js({'mode': 'open'}))
                self.element.shadowRoot.innerHTML = '<div>hello</div>'

        js.document.body.innerHTML = '<comp-test_inheritance_with_explicit_tag_name></comp-test_inheritance_with_explicit_tag_name>'

        element = js.document.body.firstElementChild

        c2 = get_component(element, Comp2)
        assert c2.some_method() == 1


def _dispose(c: Component):
    """this is needed because of the split between js and python GC (garbage collector)"""
    c.dispose()


def test_show_underling_wasm_js_pyodide_limitation(self):
    class Some: ...

    fin = []

    def do():
        from pyodide.ffi import create_proxy
        jso = js.document.createElement('div')
        pyo = Some()
        pyo_proxy = create_proxy(pyo)
        jso._py = pyo_proxy
        pyo._js = jso  # circular reference done

        weakref.finalize(pyo, lambda: fin.append(1))
        return pyo_proxy

    pyo_proxy = do()

    assert fin == []  # if the two environments js/pyodide had a conjunction to dispose the object, it would be 1

    pyo_proxy.destroy()

    assert fin == [1]


class TestDispose:

    def test_dispose_py(self):
        class Comp1(Component): ...

        fin = []

        def do():
            comp1 = Comp1()
            weakref.finalize(comp1, lambda: fin.append(1))
            _dispose(comp1)

        do()

        assert fin == [1]

    def test_dispose_js(self):
        class Comp1(Component): ...

        fin = []

        def do():
            ele1 = js.document.createElement(Comp1.component_metadata.tag_name)
            comp1 = from_element(ele1)
            weakref.finalize(comp1, lambda: fin.append(1))
            _dispose(comp1)

        do()

        assert fin == [1]


def test_class_full_name():
    class Comp1(Component):
        pass

    logger.debug(f'class=`{Comp1}`')
    assert Comp1.component_metadata.class_full_name == __name__ + '.' + Comp1.__qualname__
