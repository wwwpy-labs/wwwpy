import shutil
from pathlib import Path

from tests.server.filesystem_sync.mutator import Mutator
from tests.server.filesystem_sync.fs_compare import FsCompare
from tests.server.filesystem_sync.sync_fixture import _deserialize_events
from wwwpy.common.filesystem.sync.event_invert_apply import events_invert, events_apply


class FilesystemFixture:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.verify_mutator_events = True

        def mk(path):
            p = tmp_path / path
            p.mkdir(parents=True, exist_ok=True)
            return p

        self.initial_fs = mk('initial')
        self.expected_fs = mk('expected')
        self.inverted_events = None
        self.events = None
        self.fs_compare = FsCompare(self.initial_fs, self.expected_fs, 'initial', 'expected')
        self.source_mutator = Mutator(self.expected_fs)
        """This transform the initial_fs into the expected_fs.
    In other words it should execute the operations that will create 
    events e_list that when applied to A_0 should result in A_n"""

    def assert_filesystem_are_equal(self):
        __tracebackhide__ = True
        assert self.fs_compare.synchronized(), self.fs_compare.sync_error()

    def invoke(self, events_str: str):
        assert self.inverted_events is None
        assert self.events is None
        self.events = _deserialize_events(events_str)

        # verify that we specified events_str correctly
        # if not self.verify_mutator_events:
        assert self.source_mutator.events == self.events

        self.invert_apply()

    def invert_apply(self):
        assert self.inverted_events is None
        assert self.events is not None

        events_fix = [e.to_absolute(self.expected_fs) for e in self.events]
        self.inverted_events = events_invert(self.expected_fs, events_fix)
        events_apply(self.initial_fs, self.inverted_events)

    @property
    def source_init(self):
        """This should be used to create the initial state of the filesystem.
        In other words this is setting up the A_0 filesystem"""

        def on_init_exit():
            shutil.rmtree(self.expected_fs, ignore_errors=True)
            shutil.copytree(self.initial_fs, self.expected_fs, dirs_exist_ok=True)

        return Mutator(self.initial_fs, on_init_exit)
