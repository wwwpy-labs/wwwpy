import logging

import js
import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def clean_document():
    _clean_document('begin')
    yield None
    _clean_document('end')


def _clean_document(mode):
    # logger.debug(f'_clean_document {mode}')
    js.document.documentElement.innerHTML = ''
    js.document.head.innerHTML = ''
    for attr in js.document.documentElement.attributes:
        js.document.documentElement.removeAttributeNode(attr)

    # logger.debug(f'body=```{js.document.body.innerHTML}```')
