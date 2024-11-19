import os
from io import BytesIO
from itertools import chain
from pathlib import Path
from typing import NamedTuple, Iterator
from zipfile import ZipFile

from wwwpy.common.iterlib import CallableToIterable
from wwwpy.resources import from_directory, PathResource, Resource, default_resource_accept, build_archive, \
    StringResource, stacktrace_pathfinder, _is_path_contained, library_resources, from_directory_lazy, ResourceIterable

parent = Path(__file__).parent


class Test_ResourceIterator_from_filesystem:
    support_data = parent / 'layer_2_support/from_filesystem'

    def test_one_file(self):
        folder = self.support_data / 'one_file'
        actual = set(from_directory(folder))
        expect = {PathResource('foo.py', folder / 'foo.py')}
        assert expect == actual

    def test_zero_file(self):
        folder = self.support_data / 'zero_file'
        folder.mkdir(exist_ok=True)  # git does not commit empty folders
        actual = set(from_directory(folder))
        expect = set()
        assert expect == actual

    def test_selective(self):
        folder = self.support_data / 'relative_to'
        actual = set(from_directory(folder / 'yes', relative_to=folder))
        expect = {PathResource('yes/yes.txt', folder / 'yes/yes.txt')}
        assert expect == actual

    def test_resource_filter(self):
        folder = self.support_data / 'resource_filter'
        reject = folder / 'yes/reject'

        pycache = folder / 'yes/__pycache__'
        pycache.mkdir(exist_ok=True)
        (pycache / 'cache.txt').write_text('some cache')

        def resource_accept(resource: Resource) -> bool:
            if resource.filepath == reject:
                return False
            return default_resource_accept(resource)

        actual = set(from_directory(folder, resource_accept=resource_accept))
        expect = {PathResource('yes/yes.txt', folder / 'yes/yes.txt')}
        assert expect == actual

    def test_lazy__no_path_available_yet(self):
        target = from_directory_lazy(folder_provider=lambda: (None, None))
        assert set(target) == set()

    def test_lazy__path_that_does_not_exist(self, tmp_path):
        tmp_path.rmdir()
        target = from_directory_lazy(folder_provider=lambda: (tmp_path, None))
        assert set(target) == set()


class Test_build_archive:
    support_data = parent / 'layer_2_support/build_archive'

    def test_build_archive(self):
        class ZFile(NamedTuple):
            filename: str
            content: bytes

        folder = self.support_data / 'simple'
        (folder / 'empty_dir').mkdir(exist_ok=True)  # should be ignored by build_archive

        archive_bytes = build_archive(chain.from_iterable(
            [from_directory(folder), [StringResource('dir1/baz.txt', "#baz")]]))

        actual_files = set()
        with ZipFile(BytesIO(archive_bytes)) as zf:
            for il in zf.infolist():
                with zf.open(il, 'r') as file:
                    actual_files.add(ZFile(il.filename, file.read()))

        expected_files = {
            ZFile('foo.txt', '#foo'.encode()),
            ZFile('dir1/bar.txt', '#bar'.encode()),
            ZFile('dir1/baz.txt', '#baz'.encode()),
        }

        assert expected_files == actual_files

    def test_build_archive_when_some_iter_raises(self):
        class ZFile(NamedTuple):
            filename: str
            content: bytes

        folder = self.support_data / 'simple'
        (folder / 'empty_dir').mkdir(exist_ok=True)  # should be ignored by build_archive

        def faulty() -> Iterator[Resource]:
            raise ValueError('some error')

        archive_bytes = build_archive(chain.from_iterable(
            [from_directory(folder), CallableToIterable(faulty), [StringResource('dir1/baz.txt', "#baz")]]))

        actual_files = set()
        with ZipFile(BytesIO(archive_bytes)) as zf:
            for il in zf.infolist():
                with zf.open(il, 'r') as file:
                    actual_files.add(ZFile(il.filename, file.read()))

        expected_files = {
            ZFile('foo.txt', '#foo'.encode()),
            ZFile('dir1/bar.txt', '#bar'.encode()),
            ZFile('dir1/baz.txt', '#baz'.encode()),
        }

        assert expected_files == actual_files


class Test_stacktrace_pathfinder:

    def test_external_filename(self):
        actual = stacktrace_pathfinder()
        assert actual == Path(__file__).resolve()

    def test_is_contained_into(self):
        assert _is_path_contained(Path('/foo/bar'), Path('/foo/bar/baz')) is False

    def test_is_contained_into_2(self):
        assert _is_path_contained(Path('/foo/xxx'), Path('/foo/bar/baz')) is False

    def test_is_contained_into_3(self):
        assert _is_path_contained(Path('/foo/bar/baz/yyy'), Path('/foo/bar/baz')) is True

    def test_is_contained_into_4(self):
        assert _is_path_contained(Path('/foo/bar/baz'), Path('/foo/bar/baz')) is True


def test_library_resources():
    expected_minimum = {'wwwpy/__init__.py', 'wwwpy/remote/__init__.py', 'wwwpy/common/__init__.py'}

    def actual_minimum(iterable):
        return expected_minimum.intersection({resource.arcname for resource in iterable})

    target = library_resources()

    assert actual_minimum(target) == expected_minimum
    assert actual_minimum(target) == expected_minimum  # use the iterable again


def test_library_resources__verify_content():
    """Should include common, remote and the wwwpy.* root files"""

    actual = {Path(resource.arcname) for resource in library_resources()}

    def is_root_entity(ent: Path):
        if len(ent.parts) == 2 and ent.parts[0] == 'wwwpy':
            return True
        return False

    actual = {ent for ent in actual if not is_root_entity(ent)}

    second_level = {ent.parts[1] for ent in actual}
    assert second_level == {'common', 'remote'}


def posix_path(path: str) -> str:
    return path.replace(os.path.sep, '/')
