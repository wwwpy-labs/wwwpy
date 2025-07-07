from pathlib import Path

_parent = Path(__file__).parent


def _svg(filename: str) -> Path: return _parent / filename


# you can control-click the icon filename to open it (at least in PyCharm)
class AllIcons:
    toolWindowComponents_dark = _svg("toolWindowComponents_dark.svg")
    properties_dark = _svg("properties_dark.svg")
    project_20x20_dark = _svg("project@20x20_dark.svg")
    structure_20x20_dark = _svg("structure@20x20_dark.svg")
    events = _svg("events.svg")
    toolWindowComponents_20x20_dark = _svg("toolWindowComponents@20x20_dark.svg")

    @classmethod
    def all_icons(cls) -> tuple[Path, ...]:
        return _all_icons


_all_icons = tuple(
    value for name, value in vars(AllIcons).items()
    if isinstance(value, Path) and not name.startswith('_')
)
