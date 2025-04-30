import dataclasses
import logging

import pytest

from wwwpy.common.designer import element_library
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.rpc import serialization

logger = logging.getLogger(__name__)


@pytest.fixture
def el():
    return element_library.element_library()


def test_element_library(el):
    assert len(el.elements) > 0


def test_basic_attributes(el):
    span = el.by_tag_name('span')
    assert span
    assert span.attributes.get('class') is not None


def test_shown_element(el):
    assert el.by_tag_name('sl-button') is not None


def test_serialization(el):
    for e in el.elements:
        e = dataclasses.replace(e)
        e.gen_html = None
        logger.debug(f'serializing {e.tag_name}')
        ser = serialization.to_json(e, ElementDef)
        deser = serialization.from_json(ser, ElementDef)
        assert e == deser


def test_unknown_element(el):
    ed = el.by_tag_name('unknown-element')
    assert ed is not None
    assert ed is el.by_tag_name('unknown-element')
