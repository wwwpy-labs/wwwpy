from __future__ import annotations

import inspect
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterator, Callable, Optional, TypeVar, Iterable, Protocol, Tuple
from zipfile import ZipFile

from wwwpy.common import iterlib, modlib, files
from wwwpy.common.iterlib import CallableToIterable

parent = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Resource(ABC):
    """represents something (a file) to be transferred to the remote"""
    arcname: str

    @abstractmethod
    def _bytes(self) -> bytes:
        pass


ResourceIterable = Iterable[Resource]
"""Let's say that the Iterable is a factory function that returns an Iterator.
https://docs.python.org/3/library/collections.abc.html<
https://wiki.python.org/moin/Iterator
"""


@dataclass(frozen=True)
class StringResource(Resource):
    content: str

    def _bytes(self) -> bytes:
        return self.content.encode('utf-8')


@dataclass(frozen=True)
class PathResource(Resource):
    filepath: Path

    def _bytes(self) -> bytes:
        raise Exception('this has a special method to get the bytes')


TResource = TypeVar("TResource", bound=Resource)

ResourceAccept = Callable[[TResource], bool]


def default_resource_accept(resource: Resource) -> bool:
    if not isinstance(resource, PathResource):
        return True
    filepath = resource.filepath
    if filepath.name == '.DS_Store':
        return False
    if filepath.is_dir() and filepath.name in files.directory_blacklist:
        return False
    return True


FilesystemIterable = Iterable[PathResource]


def from_file(file: Path, relative_to: Path) -> FilesystemIterable:
    def bundle() -> Iterator[PathResource]:
        rel = file.relative_to(relative_to)
        if file.is_file() and file.exists():
            yield PathResource(str(rel), file)

    return CallableToIterable(bundle)


def _recurse(path: Path, relative_to: Path, resource_accept: ResourceAccept) -> Iterator[PathResource]:
    for f in path.glob('*'):
        rel = f.relative_to(relative_to).as_posix()
        candidate = PathResource(rel, f)
        if resource_accept(candidate):
            if f.is_file():
                yield candidate
            else:
                yield from _recurse(f, relative_to, resource_accept)


def from_directory(
        folder: Path, relative_to: Path | None = None,
        resource_accept: ResourceAccept = default_resource_accept
) -> FilesystemIterable:
    return from_directory_lazy(lambda: (folder, relative_to), resource_accept)


class FolderProvider(Protocol):
    """Return tuple of two Paths[folder, relative_to]. Both are optional"""

    def __call__(self) -> Tuple[Path | None, Path | None]: ...


def from_directory_lazy(
        folder_provider: FolderProvider,
        resource_accept: ResourceAccept = default_resource_accept
) -> FilesystemIterable:
    def bundle() -> Iterator[PathResource]:
        folder, relative_to = folder_provider()
        if folder is None:
            return
        rel_to: Path = folder if relative_to is None else relative_to
        yield from _recurse(folder, rel_to, resource_accept)

    return CallableToIterable(bundle)


def build_archive(resource_iterator: Iterator[Resource]) -> bytes:
    """builds a zip archive from the given resources and returns the bytes"""

    stream = BytesIO()
    zip_file = ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1)
    for resource in iterlib.iter_catching(resource_iterator):
        if isinstance(resource, PathResource):
            zip_file.write(resource.filepath, resource.arcname)
        elif isinstance(resource, Resource):
            zip_file.writestr(resource.arcname, resource._bytes())
        else:
            raise Exception(f'Unhandled class \n  type={type(resource).__name__} \n  data={resource}')
    zip_file.close()

    stream.seek(0)
    return stream.getbuffer().tobytes()


def stacktrace_pathfinder(stack_backtrack: int = 1) -> Optional[Path]:
    wwwpy_root = parent

    for stack in inspect.stack():
        source_path = Path(stack.filename).resolve()
        if not _is_path_contained(source_path, wwwpy_root):
            stack_backtrack -= 1
            if stack_backtrack == 0:
                return source_path

    return None


def _is_path_contained(child: Path, parent: Path) -> bool:
    cl = len(child.parts)
    cp = len(parent.parts)
    if cl < cp:
        return False
    m = min(cl, cp)
    child_parts = child.parts[:m]
    parent_parts = parent.parts[:m]
    return child_parts == parent_parts


def library_resources() -> Iterable[PathResource]:
    """returns the resources from the wwwpy library itself"""

    # return from_directory(parent, relative_to=parent.parent)
    def accept(resource: Resource) -> bool:
        if not default_resource_accept(resource):
            return False
        path = Path(resource.arcname)
        if path.parts[0] != 'wwwpy':
            return False
        if len(path.parts) == 2:
            return True  # wwwpy/* root files
        return path.parts[1] in {'common', 'remote'}

    return from_directory_lazy(lambda: (parent, parent.parent), accept)


def _fs_iterable(package_name: str) -> Tuple[Path | None, Path | None]:
    target = modlib._find_package_directory(package_name)
    if not target:
        return None, None
    root = target.parent
    r = range(package_name.count('.'))
    for _ in r:
        root = root.parent

    return target, root


def from_module_lazy(module_name: str):
    return from_directory_lazy(lambda: _fs_iterable(module_name))
