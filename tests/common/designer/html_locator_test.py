import wwwpy.common.designer.html_locator as html_locator
from wwwpy.common.designer import html_parser
from wwwpy.common.designer.html_locator import Node


def test_locate():
    # language=html
    html = "<div id='foo'><div></div><div id='target'></div></div>"
    path = [Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]
    actual = html_locator.locate_span(html, path)
    expect = (25, 48)
    assert actual == expect


def test_serde():
    path = [Node("div", -1, {}), Node("div", 0, {'id': 'foo'}), Node("div", 1, {'id': 'target'})]
    serialized = html_locator.node_path_serialize(path)
    # print on stder
    print(f'\nserialized=={serialized}', )
    deserialized = html_locator.node_path_deserialize(serialized)

    assert path == deserialized, f'\nexpect={path} \ndeserialized={deserialized}'


def test_cst_node_to_node():
    # language=html
    html = "<b></b><div id='foo'><input><br><button id='btn1' disabled></button></div>"
    tree = html_parser.html_to_tree(html)
    actual = html_locator.tree_to_path(tree, [1, 2])
    expect = [Node("div", 1, {'id': 'foo'}), Node("button", 2, {'id': 'btn1', 'disabled': None})]
    assert actual == expect


def test_cst_node_to_node_negative_notation():
    # language=html
    html = "<b></b><div id='foo'><input><br><button id='btn1' disabled></button></div><br>"
    tree = html_parser.html_to_tree(html)
    actual = html_locator.tree_to_path(tree, [-2, -1])
    expect = [Node("div", 1, {'id': 'foo'}), Node("button", 2, {'id': 'btn1', 'disabled': None})]
    assert actual == expect


class TestTreeFuzzyMatch:
    def test_dynamically_inserted_tag(self):
        # GIVEN
        # language=html
        source_html = """
<form id="f1">
    <input id="i1" title="title1" required type="text">
    <button id="b1" type="submit">b1-content</button>
    <textarea id="ta1" rows="10">ta1-content</textarea>
</form>
<span><br><button>confounder</button></span>
"""
        # language=html
        dyn_insertion = "<div></div>"
        live_tree = html_parser.html_to_tree(dyn_insertion + source_html)
        live_path = html_locator.tree_to_path(live_tree, [1, 1])  # [ 1=form, 1=button ]

        # WHEN
        actual = html_locator.rebase_path(source_html, live_path)

        # THEN
        expect = html_locator.tree_to_path(html_locator.html_to_tree(source_html), [0, 1])  # [ 0=form, 1=button ]
        assert actual == expect, f'\nactual={actual} \nexpect={expect}'

    def todo_test_nested_divs(self):
        # language=html
        source_html = """<div><div><div></div></div></div>"""
        live_html = """<div><div><div></div></div></div>"""
        live_tree = html_parser.html_to_tree(live_html)
        live_path = html_locator.tree_to_path(live_tree, [0, 0, 0])

        # WHEN
        actual = html_locator.rebase_path(source_html, live_path)

        # THEN
        expect = html_locator.tree_to_path(html_locator.html_to_tree(source_html), [0, 0, 0])
        assert actual == expect, f'\nactual={actual} \nexpect={expect}'

    def todo_test_swapped_tags(self):
        # language=html
        source_html = """<div><button class='a'></button></div><div><button></button></div>"""
        # language=html
        live_html = """<div><button></button></div><div><button class='a'></button></div>"""


def _node_sim(html1: str, html2: str) -> float:
    tree1 = html_parser.html_to_tree(html1)
    tree2 = html_parser.html_to_tree(html2)
    similarity = html_locator.node_similarity(tree1[0], tree2[0])
    return similarity


class TestNodeSimilarity:

    def test_name_tag(self):
        # language=html
        assert _node_sim("<input>", "<input>") == 1.0

    def test_one_diff_attr(self):
        # language=html
        assert 0.1 < _node_sim("<input class='a'>", "<input class='b'>") < 1.0

    def test_data_name_same(self):
        # language=html
        assert (
                _node_sim("<div data-name='foo' class='a'></div>", "<div data-name='foo' class='b'></div>") >
                _node_sim("<input class='a'>", "<input class='a'>")
        )

    def test_data_name_different(self):
        # language=html
        assert (
                _node_sim("<div data-name='foo1' class='a'></div>", "<div data-name='foo2' class='b'></div>") <
                _node_sim("<input class='a'>", "<input class='b'>")
        )

    def todo_test_with_level(self):
        divs = "<div><div><div></div></div></div>"
        tree1 = html_parser.html_to_tree(divs)
        tree2 = html_parser.html_to_tree(divs)
        sim_0_0 = html_locator.node_similarity(tree1[0], tree2[0])
        sim_0_00 = html_locator.node_similarity(tree1[0], tree2[0].children[0])
        sim_0_000 = html_locator.node_similarity(tree1[0], tree2[0].children[0].children[0])
        assert (sim_0_0 > sim_0_00)
        assert (sim_0_00 > sim_0_000)

    def test_different_tags(self):
        # language=html
        assert (
                _node_sim("<div></div>", "<span></span>") < 0.1
        )
# todo different tags, e.g., div vs span; different levels
