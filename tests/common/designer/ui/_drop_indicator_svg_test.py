import xml.etree.ElementTree as ET

from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.ui._drop_indicator_svg import svg_indicator_for


def test_valid_xml():
    for p in Position:
        # xml_string = '<root><child>text</child></root>'
        xml_string = svg_indicator_for(p)
        root = ET.fromstring(xml_string)
        assert root.tag == '{http://www.w3.org/2000/svg}svg'


def test_svg_should_be_different_from_each_other():
    a, b, c = map(svg_indicator_for, Position)
    assert a != b
    assert a != c
    assert b != c
