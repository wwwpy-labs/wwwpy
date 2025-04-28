import js
import pytest
from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib


def test_win_eq():
    assert js.window == js.window
    assert getattr(js, 'window') == getattr(js, 'window')
    assert getattr(js, 'window').js_id == getattr(js, 'window').js_id
    assert getattr(js, 'document').js_id == getattr(js, 'document').js_id


def test_create_proxy_assumptions():
    class C1:
        def m1(self):
            pass

    c1 = C1()
    m1 = c1.m1
    assert create_proxy(c1.m1) is not m1
    assert create_proxy(c1.m1) is not create_proxy(c1.m1)


def test_accept_1():
    target = eventlib.convention_accept('_js_window__click')
    assert target == eventlib.Accept(js.window, 'click')


def test_accept_2():
    target = eventlib.convention_accept('_js_document__keydown')
    assert target == eventlib.Accept(js.document, 'keydown')


def test_accept_reject():
    assert eventlib.convention_accept('_js_window_click') is None
    assert eventlib.convention_accept('js_window__click') is None
    assert eventlib.convention_accept('_js_window__') is None


def test_add_event():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 1


def test_add_remove():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)
    eventlib.remove_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 0


def test_double_add_event():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)
    eventlib.add_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 1


def test_double_add_event_and_one_remove():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)
    eventlib.add_event_listeners(c1)
    eventlib.remove_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 1


def test_double_remove_event():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)
    eventlib.add_event_listeners(c1)
    eventlib.remove_event_listeners(c1)
    eventlib.remove_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 0


def test_remove_event():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.add_event_listeners(c1)
    eventlib.remove_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 0


class TestHandler:

    async def test_install(self):
        # GIVEN
        events = []

        class C1:
            @eventlib.handler_options(target=js.document, type='click')
            def handler1(self, e):
                events.append(e)

        c1 = C1()

        # WHEN
        eventlib.handler(c1.handler1).install()
        js.document.body.click()

        # THEN
        assert len(events) == 1

    async def test_double_install(self):
        # GIVEN
        events = []

        class C1:
            @eventlib.handler_options(target=js.document, type='click')
            def handler1(self, e):
                events.append(e)

        c1 = C1()

        # WHEN
        eventlib.handler(c1.handler1).install()

        # THEN
        with pytest.raises(Exception):
            eventlib.handler(c1.handler1).install()

    async def test_handler_same_instance(self):
        # GIVEN
        class C1:
            @eventlib.handler_options(target=js.document, type='click')
            def handler1(self, e):
                pass

        c1 = C1()

        # WHEN
        h1 = eventlib.handler(c1.handler1)
        h2 = eventlib.handler(c1.handler1)

        # THEN
        assert h1 is h2
        assert c1.handler1

    async def test_uninstall(self):
        # GIVEN
        events = []

        class C1:
            @eventlib.handler_options(target=js.document, type='click')
            def handler1(self, e):
                events.append(e)

        c1 = C1()

        # WHEN
        h = eventlib.handler(c1.handler1)
        h.install()
        h.uninstall()
        js.document.body.click()

        # THEN
        assert len(events) == 0

    async def test_uninstall_without_install(self):
        # GIVEN
        class C1:
            @eventlib.handler_options(target=js.document, type='click')
            def handler1(self, e): ...

        c1 = C1()

        # WHEN
        h = eventlib.handler(c1.handler1)

        # THEN
        with pytest.raises(Exception):
            h.uninstall()
