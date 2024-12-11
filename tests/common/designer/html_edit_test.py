from wwwpy.common.designer.html_edit import html_add, Position, html_edit, html_attribute_set, html_attribute_remove, \
    html_content_set
from wwwpy.common.designer.html_locator import Node

# language=html
html = "<div id='foo'><div></div><div id='target'></div></div>"
path = [Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]


def test_add_beforebegin():
    actual = html_add(html, 'xyz', path, Position.beforebegin)
    # language=html
    assert actual == "<div id='foo'><div></div>xyz<div id='target'></div></div>"


def test_add_afterend():
    actual = html_add(html, 'xyz', path, Position.afterend)
    # language=html
    assert actual == "<div id='foo'><div></div><div id='target'></div>xyz</div>"


def test_edit():
    actual = html_edit(html, 'xyz', path)
    # language=html
    assert actual == "<div id='foo'><div></div>xyz</div>"


class TestAttributeSet:
    def test_attribute_set(self):
        actual = html_attribute_set(html, path, 'id', 'bar')
        # language=html
        assert actual == "<div id='foo'><div></div><div id='bar'></div></div>"

    def test_attribute_set_should_not_change_quote_char(self):
        # language=html
        html = """<div id="foo"><div></div><div id="target"></div></div>"""
        path = [Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]

        actual = html_attribute_set(html, path, 'id', 'bar')
        # language=html
        assert actual == """<div id="foo"><div></div><div id="bar"></div></div>"""

    def test_attribute_correct_escaping(self):
        actual = html_attribute_set(html, path, 'id', '<div1>')
        # language=html
        assert actual == "<div id='foo'><div></div><div id='&lt;div1&gt;'></div></div>"

    def test_attribute_set_None_value(self):
        path = [Node("button", 0, {'foo': '1'})]
        # language=html
        actual = html_attribute_set("<some foo='1'></some>", path, 'foo', None)
        # language=html
        assert actual == "<some foo></some>"

    def test_from_None_attribute_to_valued(self):
        path = [Node("some", 0, {'foo': None})]
        # language=html
        actual = html_attribute_set("<some foo></some>", path, 'foo', '123')
        # language=html
        assert actual == '<some foo="123"></some>'

    def test_from_missing_to_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some></some>", path, 'foo', '123')
        # language=html
        assert actual == '<some foo="123"></some>'

    def test_from_missing_to_None_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some></some>", path, 'foo', None)
        # language=html
        assert actual == '<some foo></some>'

    def test_pre_existing_add_None_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some bar='yes'></some>", path, 'foo', None)
        # language=html
        assert actual == "<some bar='yes' foo></some>"

    def test_pre_existing_add_valued(self):
        path = [Node("some", 0, {})]
        # language=html
        actual = html_attribute_set("<some bar='yes'></some>", path, 'foo', 'xyz')
        # language=html
        assert actual == """<some bar='yes' foo="xyz"></some>"""


class TestAttributeRemove:

    def test_valued_attr(self):
        path = [Node("div", 0, {'id': 'foo'})]
        # language=html
        actual = html_attribute_remove("<div id='foo'></div>", path, 'id')
        # language=html
        assert actual == "<div></div>"

    def test_None_valued_attr(self):
        path = [Node("div", 0, {'id': None})]
        # language=html
        actual = html_attribute_remove("<div id></div>", path, 'id')
        # language=html
        assert actual == "<div></div>"

    def test_None_valued_attr_many_spaces(self):
        path = [Node("div", 0, {'id': None})]
        # language=html
        actual = html_attribute_remove("<div  id   ></div>", path, 'id')
        # language=html
        assert actual == "<div></div>"

    def test_missingAttr(self):
        path = [Node("div", 0, {'id': None})]
        # language=html
        actual = html_attribute_remove("<div id></div>", path, 'foo')
        # language=html
        assert actual == "<div id></div>"

    def test_multiple_attributes__first_no_space_after(self):
        path = [Node("div", 0, {'id': 'foo', 'class': 'bar'})]
        # language=html
        actual = html_attribute_remove("<div id='foo'class='bar'></div>", path, 'id')
        # language=html
        assert actual == "<div class='bar'></div>"

    def test_multiple_attributes__first_yes_space_after(self):
        path = [Node("div", 0, {'id': 'foo', 'class': 'bar'})]
        # language=html
        actual = html_attribute_remove("<div id='foo' class='bar'></div>", path, 'id')
        # language=html
        assert actual == "<div class='bar'></div>"

    def test_multiple_attributes__last_no_space_at_all(self):
        path = [Node("div", 0, {'id': 'foo', 'class': 'bar'})]
        # language=html
        actual = html_attribute_remove("<div class='bar'id='foo'></div>", path, 'id')
        # language=html
        assert actual == "<div class='bar'></div>"

    def test_multiple_attributes__last_no_space_after(self):
        path = [Node("div", 0, {'id': 'foo', 'class': 'bar'})]
        # language=html
        actual = html_attribute_remove("<div class='bar' id='foo'></div>", path, 'id')
        # language=html
        assert actual == "<div class='bar'></div>"


class TestContentSet:

    def test_content_set(self):
        path = [Node("div", 0, {})]
        # language=html
        actual = html_content_set("<div>old</div>", path, "new")
        # language=html
        assert actual == "<div>new</div>"
