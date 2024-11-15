import pytest
from js import document
import js
import logging
from wwwpy.remote.designer.ui.button_tab import ButtonTab, Tab

logger = logging.getLogger(__name__)

@pytest.fixture
def target():
    target = ButtonTab()
    document.body.innerHTML = ''
    document.body.appendChild(target.element)
    try:
        yield target
    finally:
        document.body.innerHTML = ''


def test_set_mixed_tabs(target):
    target.tabs = [Tab('Tab1'), 'Tab2']

    html = target.root_element().innerHTML
    assert 'Tab1' in html
    assert 'Tab2' in html


def test_click_event(target):
    # GIVEN
    target.tabs = ['Tab1', 'Tab2']
    tab_click = []

    def on_selected(tab):
        tab_click.append(tab.text)

    for t in target._tabs:
        t.on_selected = on_selected

    # WHEN
    target.tabs[0].root_element().click()
    assert tab_click == ['Tab1']

    target.tabs[1].root_element().click()
    assert tab_click == ['Tab1', 'Tab2']


def test_click_event_on_tab(target):
    # GIVEN
    tab_click = []
    target.tabs = [Tab('Tab1', on_selected=lambda tab: tab_click.append(tab.text))]

    # WHEN
    target.tabs[0].root_element().click()
    assert tab_click == ['Tab1']


def test_selection(target):
    # GIVEN
    target.tabs = ['Tab1', 'Tab2']

    # WHEN
    tab1 = target.tabs[0]
    tab2 = target.tabs[1]

    logger.warning('follow with tab1.click()')
    tab1.root_element().click()

    assert tab1.selected
    assert not tab2.selected

    logger.warning('follow with tab2.click()')
    tab2.root_element().click()

    assert not tab1.selected, target.root_element().innerHTML
    assert tab2.selected, target.root_element().innerHTML
