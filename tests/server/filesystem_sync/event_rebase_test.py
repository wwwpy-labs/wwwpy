from typing import List

from tests.server.filesystem_sync.filesystem_fixture import FilesystemFixture, fixture
from wwwpy.common.filesystem import sync
from wwwpy.common.filesystem.sync import event_rebase


def test_root_file_should_not_fire_remote_notification(fixture: FilesystemFixture):
    with fixture.source_mutator as m:
        m.touch('foo.txt')

    actual = event_rebase.filter_by_directory(fixture.source_mutator.events, {'some'})

    assert actual == []


def test_pertinent_change_should_be_included(fixture: FilesystemFixture):
    with fixture.source_mutator as m:
        m.write('foo.txt', 'content')

    actual = event_rebase.filter_by_directory(fixture.source_mutator.events, {''})

    assert sync.Event('modified', False, 'foo.txt') in actual


def test_pertinent_multiple_change_should_be_included(fixture: FilesystemFixture):
    with fixture.source_mutator as m:
        m.write('foo.txt', 'content')
        m.mkdir('p1')
        m.mkdir('p2')
        m.write('p1/p1.txt', 'content')
        m.write('p2/p2.txt', 'content')

    actual = event_rebase.filter_by_directory(fixture.source_mutator.events, {'p1', 'p2'})

    assert sync.Event('modified', False, 'p1/p1.txt') in actual
    assert sync.Event('modified', False, 'p2/p2.txt') in actual
    assert sync.Event('modified', False, 'foo.txt') not in actual
