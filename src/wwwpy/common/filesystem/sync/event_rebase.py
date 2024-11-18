from __future__ import annotations

from pathlib import Path
from typing import List, Set

from wwwpy.common.filesystem import sync


def filter_by_directory(events: List[sync.Event], directory_set: Set[str | Path]) -> List[sync.Event]:
    """Rebase events that falls in directory_set.
    It will retain the original path because the events will be used to send sync content to the remote;
    so the files still need to be accessible."""
    new_events = []
    path_set = {Path(d) for d in directory_set}

    def accept(event: sync.Event) -> bool:
        src_path = Path(event.src_path)
        for path in path_set:
            if src_path.is_relative_to(path):
                return True
        return False

    for event in events:
        if accept(event):
            new_events.append(event)
    return new_events
