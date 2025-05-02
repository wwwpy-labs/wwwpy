import js

from tests.remote.remote_fixtures import clean_document
from wwwpy.remote._elementlib import ensure_tag_instance


class Test_ensure_tag_instance:
    def test_in_body(self, clean_document):
        element1 = ensure_tag_instance('div', 'test_id', js.document.body)
        element2 = ensure_tag_instance('div', 'test_id', js.document.body)

        assert element1 == element2

    def test_in_head(self, clean_document):
        element1 = ensure_tag_instance('style', 'test_id', js.document.head)
        element2 = ensure_tag_instance('style', 'test_id', js.document.head)

        assert element1 == element2
