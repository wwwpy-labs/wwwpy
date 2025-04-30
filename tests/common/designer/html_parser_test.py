from wwwpy.common.designer.html_parser import html_to_tree, CstNode, CstAttribute, CstTree


def test_html_to_tree_empty():
    assert html_to_tree('') == []


def test_html_to_tree():
    actual = html_to_tree('<div></div>')
    expect = [CstNode(tag_name='div', span=(0, 11), attr_span=(4, 4), content_span=(5, 5))]
    assert actual == expect

    assert actual[0].content == ''


def test_nested():
    actual = html_to_tree('<div><p></p></div>')
    node_list = CstTree([CstNode(tag_name='p', span=(5, 12), attr_span=(7, 7), content_span=(8, 8))])
    expect = [CstNode(tag_name='div', span=(0, 18), attr_span=(4, 4), content_span=(5, 12), children=node_list)]
    assert actual == expect

    actual_div = actual[0]
    actual_p = actual_div.children[0]
    assert actual_div.parent is None
    assert actual_div.level == 0
    assert actual_p.parent == actual_div
    assert actual_p.level == 1

    assert actual_div.content == '<p></p>'
    assert actual_p.content == ''

    assert actual_div.child_index == 0
    assert actual_p.child_index == 0


def test_nested_with_attributes_and_spaces():
    actual = html_to_tree('<div   id="div1" > <p ></p> </div> ')
    children = CstTree([CstNode(tag_name='p', span=(19, 27), attr_span=(21, 22), content_span=(23, 23))])
    attributes_list = [CstAttribute('id', 'div1', (7, 9), (10, 16), 0)]
    expect = [CstNode(tag_name='div', span=(0, 34), attr_span=(4, 17), content_span=(18, 28)
                      , attributes_list=attributes_list, children=children)]
    assert actual == expect

    assert actual[0].content == ' <p ></p> '


def test_attribute_without_value():
    actual = html_to_tree('<div foo></div>')
    attrs = [CstAttribute('foo', None, (5, 8), None, 0)]
    expect = [CstNode(tag_name='div', span=(0, 15), attr_span=(4, 8), content_span=(9, 9), attributes_list=attrs)]
    assert actual == expect


def test_void_tags():
    actual = html_to_tree('<div><input></div>')
    expect = [CstNode(tag_name='div', span=(0, 18), attr_span=(4, 4), content_span=(5, 12),
                      children=CstTree([CstNode(tag_name='input', span=(5, 12), attr_span=(11, 11))]))]
    assert actual == expect
    assert actual[0].content == '<input>'


def test_void_tags_with_attributes_and_spaces():
    actual = html_to_tree('<div>@<input id= "input1"  ></div>'.replace('@', '\n'))
    attrs = [CstAttribute('id', 'input1', (13, 15), (17, 25), 0)]
    children = CstTree([CstNode(tag_name='input', span=(6, 28), attr_span=(12, 12 + 15), attributes_list=attrs)])
    expect = [CstNode(tag_name='div', span=(0, 34), attr_span=(4, 4), content_span=(5, 28), children=children)]
    assert actual == expect


def test_attributes_with_escaped_values():
    actual = html_to_tree('<div id="&lt;div1&gt;"></div>')
    expect = [CstNode(tag_name='div', span=(0, 29), attr_span=(4, 22), content_span=(23, 23),
                      attributes_list=[CstAttribute('id', '<div1>', (5, 7), (8, 22), 0)])]
    assert actual == expect


def test_attributes_two():
    actual = html_to_tree('<div id="div1" class="cls1"></div>')
    attrs = [CstAttribute('id', 'div1', (5, 7), (8, 14), 0), CstAttribute('class', 'cls1', (15, 20), (21, 27), 1)]
    expect = [CstNode(tag_name='div', span=(0, 34), attr_span=(4, 27), content_span=(28, 28), attributes_list=attrs)]
    assert actual == expect


def test_issue20240727():
    # language=html
    actual = html_to_tree("<div><input/></div><input>")
    expect = [CstNode(tag_name='div', span=(0, 19), attr_span=(4, 4), content_span=(5, 13),
                      children=CstTree([CstNode(tag_name='input', span=(5, 13), attr_span=(11, 11))])),
              CstNode(tag_name='input', span=(19, 26), attr_span=(25, 25))]
    assert actual == expect
    assert actual[0].content == '<input/>'


def test_issue20250118_bday():
    # language=html
    actual = html_to_tree("""\n<div><sl-button data-name="slButton1">slButton1</sl-button></div>""")
    c00 = actual[0].children[0]
    assert c00.content_span == (39, 48)
    assert c00.content == 'slButton1'


def test_child_index():
    # language=html
    actual = html_to_tree("<div><br><br></div><input>")
    assert actual[0].child_index == 0
    assert actual[1].child_index == 1
    div = actual[0]
    assert div.children[0].child_index == 0
    assert div.children[1].child_index == 1


def test_attribute_span_for_autoclosing():
    # language=html
    actual = html_to_tree("<input/>")
    assert actual == [CstNode(tag_name='input', span=(0, 8), attr_span=(6, 6))]


def _clean(tree: CstTree) -> CstTree:
    for node in tree:
        node.parent = None
        node.level = 0
        _clean(node.children)
    return tree


def test_html_comment():
    # language=html
    actual = html_to_tree("""<!-- comment -->""")
    expect = []
    assert actual == expect


def test_html_comment_something_before():
    # language=html
    actual = html_to_tree("""<!-- comment --><br>""")
    expect = [CstNode(tag_name='br', span=(16, 20), attr_span=(19, 19)), ]
    assert actual == expect


def test_autoclosing_non_void():
    # language=html
    actual = html_to_tree("""<some-tag/>""")
    expect = [CstNode(tag_name='some-tag', span=(0, 11), attr_span=(9, 9))]
    assert actual == expect


def test_autoclosing_void():
    # language=html
    actual = html_to_tree("""<br/>""")  # this is not valid but we support it
    expect = [CstNode(tag_name='br', span=(0, 5), attr_span=(3, 3))]
    assert actual == expect
