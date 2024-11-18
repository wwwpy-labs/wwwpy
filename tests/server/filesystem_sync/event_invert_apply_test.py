"""
e_list = [e_1, e_2, e_n ]

E_list = event_invert(A_n, e_list)
A_n = event_apply(A_0, E_list)

The tests of this module are created with the following steps:
- GIVEN
    - the initial state of the filesystem A_0
    - the events E_list
    - the expected state of the filesystem after the event is applied A_n
- WHEN invoke target
- THEN assert the result
"""
from pathlib import Path

import pytest

from tests.server.filesystem_sync.filesystem_fixture import FilesystemFixture
from wwwpy.common.filesystem.sync import Event


@pytest.fixture
def target(tmp_path):
    print(f'\ntmp_path file://{tmp_path}')
    fixture = FilesystemFixture(tmp_path)
    yield fixture


def test_new_file(target):
    # GIVEN
    with target.source_mutator as m:
        m.touch('new_file.txt')

    # WHEN
    target.invoke("""{"event_type": "created", "is_directory": false, "src_path": "new_file.txt"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert (target.initial_fs / 'new_file.txt').exists()


def test_delete_file(target):
    # GIVEN
    with target.source_init as m:
        m.touch('file.txt')

    with target.source_mutator as m:
        m.unlink('file.txt')

    # WHEN
    target.invoke("""{"event_type": "deleted", "is_directory": false, "src_path": "file.txt"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'file.txt').exists()


def test_new_directory(target):
    # GIVEN
    with target.source_mutator as m:
        m.mkdir('new_dir')

    # WHEN
    target.invoke("""{"event_type": "created", "is_directory": true, "src_path": "new_dir"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert (target.initial_fs / 'new_dir').exists()
    assert (target.initial_fs / 'new_dir').is_dir()


def test_delete_directory(target):
    # GIVEN
    with target.source_init as m:
        m.mkdir('dir')

    with target.source_mutator as m:
        m.rmdir('dir')

    # WHEN
    target.invoke("""{"event_type": "deleted", "is_directory": true, "src_path": "dir"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'dir').exists()


def test_move_file(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')

    with target.source_mutator as m:
        m.move('f.txt', 'f2.txt')

    # WHEN
    target.invoke("""{"event_type": "moved", "is_directory": false, "src_path": "f.txt", "dest_path": "f2.txt"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'f.txt').exists()
    assert (target.initial_fs / 'f2.txt').exists()


def test_move_directory(target):
    # GIVEN
    with target.source_init as m:
        m.mkdir('dir')

    with target.source_mutator as m:
        m.move('dir', 'dir2')

    # WHEN
    target.invoke("""{"event_type": "moved", "is_directory": true, "src_path": "dir", "dest_path": "dir2"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'dir').exists()
    assert (target.initial_fs / 'dir2').exists()
    assert (target.initial_fs / 'dir2').is_dir()


def test_move_file_to_directory(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')
        m.mkdir('dir')

    with target.source_mutator as m:
        m.move('f.txt', 'dir/f.txt')

    # WHEN
    target.invoke("""{"event_type": "moved", "is_directory": false, "src_path": "f.txt", "dest_path": "dir/f.txt"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'f.txt').exists()
    assert (target.initial_fs / 'dir/f.txt').exists()


def test_change_file_text(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')

    with target.source_mutator as m:
        m.write('f.txt', 'new content')

    # WHEN
    target.invoke("""{"event_type": "modified", "is_directory": false, "src_path": "f.txt"}""")

    # THEN
    assert Path(target.initial_fs / 'f.txt').read_text() == 'new content'
    target.assert_filesystem_are_equal()


def test_change_file_binary(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')

    with target.source_mutator as m:
        m.write('f.txt', b'\x80\x81\x82')

    # WHEN
    target.invoke("""{"event_type": "modified", "is_directory": false, "src_path": "f.txt"}""")

    # THEN
    assert Path(target.initial_fs / 'f.txt').read_bytes() == b'\x80\x81\x82'
    target.assert_filesystem_are_equal()


def test_create_modify_rename(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')

    with target.source_mutator as m:
        m.write('f.txt', 'new content')
        m.move('f.txt', 'f2.txt')

    # WHEN
    target.invoke("""
    {"event_type": "modified", "is_directory": false, "src_path": "f.txt"}\n
    {"event_type": "moved", "is_directory": false, "src_path": "f.txt", "dest_path": "f2.txt"}""")

    # THEN
    assert Path(target.initial_fs / 'f2.txt').read_text() == 'new content'
    target.assert_filesystem_are_equal()


def test_create_modify_rename_folder(target):
    # GIVEN
    with target.source_init as m:
        m.mkdir('dir')

    with target.source_mutator as m:
        m.write('dir/f.txt', 'new content')
        m.move('dir', 'dir2')

    # WHEN
    target.invoke("""
    {"event_type": "modified", "is_directory": false, "src_path": "dir/f.txt"}\n
    {"event_type": "moved", "is_directory": true, "src_path": "dir", "dest_path": "dir2"}""")

    # THEN
    assert Path(target.initial_fs / 'dir2/f.txt').read_text() == 'new content'
    target.assert_filesystem_are_equal()


def test_rename_move_file(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')
        m.mkdir('dir')

    with target.source_mutator as m:
        m.move('f.txt', 'dir/f2.txt')

    # WHEN
    target.invoke("""{"event_type": "moved", "is_directory": false, "src_path": "f.txt", "dest_path": "dir/f2.txt"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'f.txt').exists()
    assert (target.initial_fs / 'dir/f2.txt').exists()


def test_rename_move_file_and_rename_dir(target):
    # GIVEN
    with target.source_init as m:
        m.touch('f.txt')
        m.mkdir('dir')

    with target.source_mutator as m:
        m.move('f.txt', 'dir/f2.txt')
        m.move('dir', 'dir2')

    # WHEN
    target.invoke("""
    {"event_type": "moved", "is_directory": false, "src_path": "f.txt", "dest_path": "dir/f2.txt"}\n
    {"event_type": "moved", "is_directory": true, "src_path": "dir", "dest_path": "dir2"}""")

    # THEN
    target.assert_filesystem_are_equal()
    assert not (target.initial_fs / 'f.txt').exists()
    assert (target.initial_fs / 'dir2/f2.txt').exists()


def test_modify_folder__should_be_ignored(target):
    # GIVEN
    with target.source_init as m:
        m.mkdir('dir')

    with target.source_mutator as m:
        m.touch('dir')

    # WHEN
    target.invoke("""{"event_type": "modified", "is_directory": true, "src_path": "dir"}""")

    # THEN
    target.assert_filesystem_are_equal()


class TestCompression:
    def test_create_delete(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.touch('f.txt')
            m.unlink('f.txt')

        # WHEN
        target.invoke("""
        {"event_type": "created", "is_directory": false, "src_path": "f.txt"}\n
        {"event_type": "deleted", "is_directory": false, "src_path": "f.txt"}""")

        # THEN
        assert target.inverted_events == [Event('deleted', False, 'f.txt')]

    def test_create_delete_create(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.touch('f.txt')
            m.unlink('f.txt')
            m.touch('f.txt')

        # WHEN
        target.invoke("""
        {"event_type": "created", "is_directory": false, "src_path": "f.txt"}\n
        {"event_type": "deleted", "is_directory": false, "src_path": "f.txt"}\n
        {"event_type": "created", "is_directory": false, "src_path": "f.txt"}""")

        # THEN
        assert target.inverted_events[-1] == Event('created', False, 'f.txt')
        assert len(target.inverted_events) < 3

    def test_delete_folder_with_files(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.mkdir('dir')
            m.touch('dir/f.txt')
            m.touch('dir/g.txt')
            m.rmdir('dir')

        # WHEN
        target.invoke("""
        {"event_type": "created", "is_directory": true, "src_path": "dir"}\n
        {"event_type": "created", "is_directory": false, "src_path": "dir/f.txt"}\n
        {"event_type": "created", "is_directory": false, "src_path": "dir/g.txt"}\n
        {"event_type": "deleted", "is_directory": true, "src_path": "dir"}""")

        # THEN
        assert target.inverted_events == [Event('deleted', True, 'dir')]

    def test_need_recursive_delete_directory(self, target):
        # GIVEN
        with target.source_init as m:
            m.mkdir('dir')
            m.touch('dir/f.txt')

        with target.source_mutator as m:
            m.touch('dir/g.txt')
            m.rmdir('dir')

        # WHEN
        target.invoke("""
        {"event_type": "created", "is_directory": false, "src_path": "dir/g.txt"}\n
        {"event_type": "deleted", "is_directory": true, "src_path": "dir"}""")

        # THEN
        assert target.inverted_events == [Event('deleted', True, 'dir')]

    def test_modify_modify__should_be_compacted(self, target):
        # GIVEN
        with target.source_init as m:
            m.touch('f.txt')

        with target.source_mutator as m:
            m.write('f.txt', 'new content')
            m.write('f.txt', 'new content2')

        # WHEN
        target.invoke("""
        {"event_type": "modified", "is_directory": false, "src_path": "f.txt"}\n
        {"event_type": "modified", "is_directory": false, "src_path": "f.txt"}""")

        # THEN
        assert target.inverted_events == [Event('modified', False, 'f.txt', content='new content2')]

    def test_modify_rename_modify(self, target):
        # GIVEN
        with target.source_init as m:
            m.mkdir('dir')

        with target.source_mutator as m:
            m.write('dir/f.txt', 'content')
            m.move('dir', 'dir2')
            m.write('dir2/f.txt', 'content2')

        # WHEN
        target.invoke("""
        {"event_type": "modified", "is_directory": false, "src_path": "dir/f.txt"}\n
        {"event_type": "moved", "is_directory": true, "src_path": "dir", "dest_path": "dir2"}\n
        {"event_type": "modified", "is_directory": false, "src_path": "dir2/f.txt"}""")

        # THEN
        assert target.inverted_events == [
            Event('moved', True, 'dir', 'dir2'),
            Event('modified', False, 'dir2/f.txt', content='content2'),
        ]
        target.assert_filesystem_are_equal()

    def test_closed_file_should_be_ignored(self, target):
        # GIVEN
        with target.source_init as m:
            m.touch('f.txt')

        with target.source_mutator as m:
            m.close('f.txt')

        # WHEN
        target.invoke("""{"event_type": "closed", "is_directory": false, "src_path": "f.txt"}""")

        # THEN
        assert target.inverted_events == []

    def test_closed_directory_should_be_ignored(self, target):
        # GIVEN
        with target.source_init as m:
            m.mkdir('dir')
        with target.source_mutator as m:
            m.close('dir')

        # WHEN
        target.invoke("""{"event_type": "closed", "is_directory": true, "src_path": "dir"}""")

        # THEN
        assert target.inverted_events == []


class TestRealEvents:
    def test_new_file(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.touch('new_file.txt')
            m.touch('')
            m.write('new_file.txt', 'content')
            m.close('new_file.txt')
            m.touch('')

        # WHEN
        target.invoke("""
          {"event_type": "created", "is_directory": false, "src_path": "new_file.txt"}
          {"event_type": "modified", "is_directory": true, "src_path": ""}
          {"event_type": "modified", "is_directory": false, "src_path": "new_file.txt"}
          {"event_type": "closed", "is_directory": false, "src_path": "new_file.txt"}
          {"event_type": "modified", "is_directory": true, "src_path": ""}""")

        # THEN
        target.assert_filesystem_are_equal()
        assert (target.initial_fs / 'new_file.txt').exists()

    def test_new_file_and_delete(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.touch('foo.txt')
            m.touch('')
            m.touch('foo.txt')
            m.close('foo.txt')

            m.touch('')
            m.write('foo.txt', 'content1')
            m.write('foo.txt', 'content2')
            m.close('foo.txt')

            m.touch('')
            m.unlink('foo.txt')
            m.touch('')
        # assert target.source_mutator.events == target.events
        # WHEN
        target.invoke("""
  {"event_type": "created", "is_directory": false, "src_path": "foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": ""}
  {"event_type": "modified", "is_directory": false, "src_path": "foo.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "foo.txt"}
  
  {"event_type": "modified", "is_directory": true, "src_path": ""}
  {"event_type": "modified", "is_directory": false, "src_path": "foo.txt"}
  {"event_type": "modified", "is_directory": false, "src_path": "foo.txt"}
  {"event_type": "closed", "is_directory": false, "src_path": "foo.txt"}
  
  {"event_type": "modified", "is_directory": true, "src_path": ""}
  {"event_type": "deleted", "is_directory": false, "src_path": "foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": ""}""")

        # THEN
        assert not (target.initial_fs / 'new_file.txt').exists()
        target.assert_filesystem_are_equal()

    def test_new_file_in_subfolder(self, target):
        # GIVEN
        with target.source_mutator as m:
            m.mkdir('sub1')
            m.touch('')
            m.touch('sub1/foo.txt')

            m.touch('sub1')
            m.created('sub1/foo.txt')  # double create!!
            m.modified('sub1')
            m.modified('sub1/foo.txt')

            m.close('sub1/foo.txt')
            m.modified('sub1')

        # WHEN
        target.invoke("""
  {"event_type": "created", "is_directory": true, "src_path": "sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": ""}
  {"event_type": "created", "is_directory": false, "src_path": "sub1/foo.txt"}
  
  {"event_type": "modified", "is_directory": true, "src_path": "sub1"}
  {"event_type": "created", "is_directory": false, "src_path": "sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "sub1"}
  {"event_type": "modified", "is_directory": false, "src_path": "sub1/foo.txt"}
  
  {"event_type": "closed", "is_directory": false, "src_path": "sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "sub1"}""")
        # THEN
        target.assert_filesystem_are_equal()
        assert (target.initial_fs / 'sub1/foo.txt').exists()

    def test_delete_folder(self, target):
        # GIVEN
        with target.source_init as m:
            m.mkdir('sub1')
            m.touch('sub1/foo.txt')

        with target.source_mutator as m:
            m.unlink('sub1/foo.txt')
            m.touch('sub1')
            m.rmdir('sub1')
            m.touch('')

        # WHEN
        target.invoke("""
  {"event_type": "deleted", "is_directory": false, "src_path": "sub1/foo.txt"}
  {"event_type": "modified", "is_directory": true, "src_path": "sub1"}
  {"event_type": "deleted", "is_directory": true, "src_path": "sub1"}
  {"event_type": "modified", "is_directory": true, "src_path": ""}""")

        # THEN
        target.assert_filesystem_are_equal()
