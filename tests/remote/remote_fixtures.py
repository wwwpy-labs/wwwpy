import js
import pytest


@pytest.fixture
def clean_document():
    _clean_document()
    yield None
    _clean_document()


def _clean_document():
    js.document.documentElement.innerHTML = ''
    js.document.head.innerHTML = ''
    for attr in js.document.documentElement.attributes:
        js.document.documentElement.removeAttributeNode(attr)
