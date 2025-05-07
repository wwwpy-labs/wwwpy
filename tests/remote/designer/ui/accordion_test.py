import js
from pyodide.ffi import create_proxy

from wwwpy.remote.component import get_component
from wwwpy.remote.designer.ui.accordion_components import AccordionContainer, AccordionSection


async def test_container_sections():
    # language=html
    js.document.body.innerHTML = """<wwwpy-accordion-container>
    
    <wwwpy-accordion-section>
        <div slot="header">h0</div>
        <div slot="panel">p0</div>
    </wwwpy-accordion-section>
    
    <wwwpy-accordion-section>
        <div slot="header">h1</div>
        <div slot="panel">p1</div>
    </wwwpy-accordion-section>
    
</wwwpy-accordion-container>"""

    accordion_element = js.document.body.firstElementChild
    accordion = get_component(accordion_element, AccordionContainer)
    assert accordion is not None

    assert len(accordion.sections) == 2
    s0, s1 = accordion.sections
    assert isinstance(s0, AccordionSection)
    assert isinstance(s1, AccordionSection)


class TestAccordionSectionStandalone:

    async def test_accordion_should_be_expanded(self):
        # language=html
        js.document.body.innerHTML = """<wwwpy-accordion-section>
        <div slot="header">h0</div>
        p0
    </wwwpy-accordion-section>"""

        section = get_component(js.document.body.firstElementChild, AccordionSection)

        assert section.expanded is False

    async def test_expand_should_get_more_space_than_collapse(self):
        # GIVEN

        # language=html
        js.document.body.innerHTML = """<wwwpy-accordion-section>
        <div slot="header">h0</div>
        panel0-content
        <wwwpy-accordion-section>
        """
        section = get_component(js.document.body.firstElementChild, AccordionSection)

        def height():
            return section.element.getBoundingClientRect().height

        h = height()

        # WHEN
        section.transition = False
        section.expanded = True

        # THEN
        assert height() > h

    async def test_event(self):
        # language=html
        js.document.body.innerHTML = """<wwwpy-accordion-section>
        <div slot="header"><span id='span1'></span></div>
        p0
    </wwwpy-accordion-section>"""

        element = js.document.body.firstElementChild
        section = get_component(element, AccordionSection)
        span1 = js.document.getElementById('span1')
        events = []
        element.addEventListener('accordion-toggle', create_proxy(lambda event: events.append(event)))

        # WHEN
        span1.click()

        # THEN
        assert section.expanded is True
        assert events != []
        event0 = events[0]
        assert event0.target == element
        assert event0.detail.section == section

    async def test_panel_should_be_visible(self):
        # language=html
        js.document.body.innerHTML = """<wwwpy-accordion-section>
        <div slot="header">h0</div>
        <span id='span1'>panel</span>
    </wwwpy-accordion-section>"""
        element = js.document.body.firstElementChild
        section = get_component(element, AccordionSection)
        section.transition = False
        section.expanded = True
        span1 = js.document.getElementById('span1')

        assert span1.getBoundingClientRect().height > 0
        assert span1.getBoundingClientRect().width > 0
