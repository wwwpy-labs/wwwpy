import shutil

import pytest

from tests.server.filesystem_sync.sync_fixture import SyncFixture
from wwwpy.common.filesystem.sync import sync_delta2
from wwwpy.server.filesystem_sync import sync_delta, sync_zip

invalid_utf8 = b'\x80\x81\x82'


@pytest.fixture(params=[sync_delta, sync_zip, sync_delta2])
def target(tmp_path, request):
    print(f'\ntmp_path file://{tmp_path}')
    fixture = SyncFixture(tmp_path, sync=request.param)
    yield fixture

# todo there are still traces of old testing code, e.g., target.start() and target.wait_at_rest(). Remove
def test_new_file(target):
    # GIVEN
    # target.start()
    (target.source / 'new_file.txt').write_text('new file')
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """

    # WHEN
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert (target.target / 'new_file.txt').exists(), target.sync_error()
    assert (target.target / 'new_file.txt').read_text() == 'new file', target.sync_error()


def test_new_file__optimize(target):
    # GIVEN
    # target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # changes = target.do_sync()
    changes = target.apply_events(events)

    # THEN
    assert (target.target / 'new_file.txt').exists(), target.sync_error()
    assert (target.target / 'new_file.txt').read_text() == 'new file2', target.sync_error()
    # todo optimize assert len(changes) == 1, target.sync_error()


def test_new_file_and_delete(target):
    # GIVEN
    # target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    (target.source / 'new_file.txt').unlink()
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "deleted", "is_directory": false, "src_path": "source/new_file.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  """
    # WHEN
    # changes = target.get_changes()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()


def test_new_file_in_subfolder(target):
    # GIVEN
    # target.start()
    sub1 = target.source / 'sub1'
    sub1.mkdir()
    (sub1 / 'foo.txt').write_text('sub-file')
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "created", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "created", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
    """
    # WHEN
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert (target.target / 'sub1/foo.txt').exists(), target.sync_error()
    assert (target.target / 'sub1/foo.txt').read_text() == 'sub-file', target.sync_error()


def test_delete_file(target):
    # GIVEN
    source_foo = target.source / 'foo.txt'
    source_foo.write_text('content1')
    target_foo = target.target / 'foo.txt'
    target_foo.write_text('content1')
    # target.start()

    source_foo.unlink()
    # target.wait_at_rest()
    events = """
  {"event_type": "deleted", "is_directory": false, "src_path": "source/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # changes = target.do_sync()
    changes = target.apply_events(events)

    # THEN
    assert not target_foo.exists(), target.sync_error()
    # todo optimize assert len(changes) == 1, target.sync_error()


def test_created(target):
    # GIVEN
    # target.start()
    (target.source / 'foo.txt').touch()
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # changes = target.do_sync()
    changes = target.apply_events(events)

    # THEN
    assert (target.target / 'foo.txt').exists(), target.sync_error()
    assert (target.target / 'foo.txt').stat().st_size == 0, target.sync_error()
    assert len(changes) == 1


def test_init(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')
    (target.source / 'foo.bin').write_bytes(invalid_utf8)

    # WHEN
    target.do_init()

    # THEN
    assert (target.target / 'foo.txt').read_text() == 'c1', target.sync_error()
    assert (target.target / 'foo.bin').read_bytes() == invalid_utf8, target.sync_error()
    assert target.synchronized(), target.sync_error()


def test_synchronized_no_files(target):
    # GIVEN

    # WHEN
    target.do_init()

    # THEN
    assert target.synchronized()
    assert target.sync_error() is None


def test_synchronized_some_files(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')

    assert target.synchronized() is False
    assert target.sync_error() is not None


def test_delete_folder(target):
    # GIVEN
    (target.source / 'sub1').mkdir()
    (target.source / 'sub1/foo.txt').write_text('content1')
    target.copy_source_to_target()
    # target.start()

    shutil.rmtree(target.source / 'sub1')
    # target.wait_at_rest()
    events = """
  {"event_type": "deleted", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "deleted", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()


def test_delete_folder__and_recreate_it(target):
    def build():
        (target.source / 'sub1').mkdir()
        (target.source / 'sub1/foo.txt').write_text('content1')

    # GIVEN
    build()
    target.copy_source_to_target()
    # target.start()

    # WHEN
    shutil.rmtree(target.source / 'sub1')
    build()
    # target.wait_at_rest()
    events = """
  {"event_type": "deleted", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "deleted", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "created", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "created", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub1"}
"""

    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()


def test_invalid_text(target):
    # GIVEN
    # target.start()

    (target.source / 'foo.bin').write_bytes(invalid_utf8)
    # target.wait_at_rest()
    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/foo.bin"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/foo.bin"}
  {"event_type": "closed", "is_directory": false, "src_path": "source/foo.bin"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()
    assert (target.target / 'foo.bin').read_bytes() == invalid_utf8


def test_rename_file(target):
    target.skip_for(sync_delta, 'not implemented')
    # GIVEN
    (target.source / 'foo.txt').write_text('content1')
    target.copy_source_to_target()
    # target.start()

    # WHEN
    (target.source / 'foo.txt').rename(target.source / 'bar.txt')
    # target.wait_at_rest()
    events = """
  {"event_type": "moved", "is_directory": false, "src_path": "source/foo.txt", "dest_path": "source/bar.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
"""
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert not (target.target / 'foo.txt').exists(), target.sync_error()
    assert (target.target / 'bar.txt').exists(), target.sync_error()
    assert (target.target / 'bar.txt').read_text() == 'content1'


def test_rename_folder(target):
    target.skip_for(sync_delta, 'not implemented')
    _skip_synth(target)
    # GIVEN
    (target.source / 'sub1').mkdir()
    (target.source / 'sub1/foo.txt').write_text('content1')
    target.copy_source_to_target()
    # target.start()

    # WHEN
    (target.source / 'sub1').rename(target.source / 'sub2')
    # target.wait_at_rest()
    events = """
  {"event_type": "moved", "is_directory": true, "src_path": "source/sub1", "dest_path": "source/sub2"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "moved", "is_directory": false, "src_path": "source/sub1/foo.txt", "dest_path": "source/sub2/foo.txt"}
"""
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()


def _skip_synth(target):
    target.skip_for(sync_delta2, 'I suspect this has synthetic events and we don''t '
                                 'need them and if they are present we crash')


def test_move_folder_in_subfolder(target):
    target.skip_for(sync_delta, 'not implemented')
    _skip_synth(target)
    # GIVEN
    (target.source / 'sub1').mkdir()
    (target.source / 'sub1/foo.txt').write_text('content1')
    (target.source / 'sub2').mkdir()
    target.copy_source_to_target()
    # target.start()

    # WHEN
    shutil.move(str(target.source / 'sub1'), str(target.source / 'sub2/'))
    # target.wait_at_rest()
    events = """
  {"event_type": "moved", "is_directory": true, "src_path": "source/sub1", "dest_path": "source/sub2/sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/sub2"}
  {"event_type": "moved", "is_directory": false, "src_path": "source/sub1/foo.txt", "dest_path": "source/sub2/sub1/foo.txt"}
"""
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert target.synchronized(), target.sync_error()


def test_issue_nr28_missing_create_folder_event(target):
    # GIVEN
    # target.start()
    project_dir = target.source
    readme_path = project_dir / 'readme.txt'
    remote_dir = project_dir / 'remote'
    remote_dir.mkdir()
    readme_path.write_text('readme content')
    (remote_dir / '__init__.py').write_text('# init file')
    (remote_dir / 'component1.py').write_text('# component code')
    # target.wait_at_rest()

    events = """
  {"event_type": "created", "is_directory": false, "src_path": "source/readme.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/readme.txt"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/readme.txt"}
  {"event_type": "created", "is_directory": false, "src_path": "source/remote/__init__.py"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/remote"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/remote/__init__.py"}
  {"event_type": "created", "is_directory": false, "src_path": "source/remote/component1.py"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/remote"}
  {"event_type": "modified", "is_directory": false, "src_path": "source/remote/component1.py"}
  {"event_type": "created", "is_directory": true, "src_path": "source/remote"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
  {"event_type": "modified", "is_directory": true, "src_path": "source/remote"}
  {"event_type": "modified", "is_directory": true, "src_path": "source"}
    """
    # WHEN
    # target.do_sync()
    target.apply_events(events)

    # THEN
    assert (target.target / 'readme.txt').exists(), target.sync_error()
    assert (target.target / 'readme.txt').read_text() == 'readme content', target.sync_error()
    assert (target.target / 'remote').exists(), target.sync_error()
    assert (target.target / 'remote' / '__init__.py').exists(), target.sync_error()
    assert (target.target / 'remote' / 'component1.py').exists(), target.sync_error()
    assert (target.target / 'remote' / '__init__.py').read_text() == '# init file', target.sync_error()
    assert (target.target / 'remote' / 'component1.py').read_text() == '# component code', target.sync_error()
