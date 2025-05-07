import logging

import js
import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def clean_document():
    clean_document_now('begin')
    yield None
    clean_document_now('end')


def clean_document_now(mode='mode/NA'):
    # logger.debug(f'_clean_document {mode}')
    js.document.documentElement.innerHTML = ''
    js.document.head.innerHTML = ''
    for attr in js.document.documentElement.attributes:
        js.document.documentElement.removeAttributeNode(attr)

    # logger.debug(f'body=```{js.document.body.innerHTML}```')
