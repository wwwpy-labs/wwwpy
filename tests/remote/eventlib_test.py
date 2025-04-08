import js
from pyodide.ffi import create_proxy

from wwwpy.remote import eventlib


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
    # events.clear()

    # eventlib.remove_event_listeners(c1)

    # js.document.body.click()

    # assert len(events) == 0


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


def test_remove_without_add():
    events = []

    class C1:
        def _js_document__click(self, e):
            events.append(e)

    c1 = C1()
    eventlib.remove_event_listeners(c1)

    js.document.body.click()

    assert len(events) == 0
