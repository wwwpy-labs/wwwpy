from wwwpy.common.designer.ui.icons.all_icons import AllIcons


def test_all_icons_exists():
    icons = AllIcons.all_icons()

    assert len(icons) > 0
    errors = [i for i in icons if not i.exists()]
    assert errors == []


def test_a_couple():
    icon_set = set(AllIcons.all_icons())
    assert len(icon_set) > 1
    assert AllIcons.toolWindowComponents_dark in icon_set
    assert AllIcons.properties_dark in icon_set
