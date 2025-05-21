import xml.etree.ElementTree as ET

from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.ui._drop_indicator_svg import svg_indicator_for, position_for


def test_valid_xml():
    for p in Position:
        # xml_string = '<root><child>text</child></root>'
        xml_string = svg_indicator_for(100, 50, p)
        root = ET.fromstring(xml_string)
        assert root.tag == '{http://www.w3.org/2000/svg}svg'


def test_svg_should_be_different_from_each_other():
    a, b, c, d = map(lambda p: svg_indicator_for(100, 50, p), Position)
    assert a != b
    assert a != c
    assert b != c
    assert a != d
    assert b != d
    assert c != d


class TestPositionFor:
    def test_beforebegin(self):
        assert position_for(100, 50, 1, 1) == Position.beforebegin

    def test_afterend(self):
        assert position_for(100, 50, 100 - 1, 50 - 1) == Position.afterend

    def test_afterbegin(self):
        assert position_for(50, 50, 25 - 1, 25 - 1) == Position.afterbegin

    def test_beforeend(self):
        assert position_for(50, 50, 25 + 1, 25 + 1) == Position.beforeend
