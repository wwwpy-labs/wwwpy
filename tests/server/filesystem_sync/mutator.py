import shutil
from pathlib import Path
from typing import List, AnyStr

from wwwpy.common.filesystem.sync import Event


class Mutator:
    def __init__(self, fs: Path, on_exit=None):
        self.fs = fs
        self.on_exit = on_exit
        self.events: List[Event] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.on_exit:
            self.on_exit()

    def touch(self, path: str):
        fs_path = self.fs / path
        event_type = 'created' if not fs_path.exists() else 'modified'
        self.events.append(Event(event_type=event_type, is_directory=fs_path.is_dir(), src_path=path))
        fs_path.touch()

    def close(self, path: str):
        fs_path = self.fs / path
        self.events.append(Event(event_type='closed', is_directory=fs_path.is_dir(), src_path=path))

    def mkdir(self, path: str):
        self.events.append(Event(event_type='created', is_directory=True, src_path=path))
        (self.fs / path).mkdir()

    def unlink(self, path: str):
        self.events.append(Event(event_type='deleted', is_directory=False, src_path=path))
        (self.fs / path).unlink()

    def rmdir(self, path):
        self.events.append(Event(event_type='deleted', is_directory=True, src_path=path))
        shutil.rmtree(self.fs / path)

    def move(self, old, new):
        fs_old = self.fs / old
        self.events.append(Event(event_type='moved', is_directory=fs_old.is_dir(), src_path=old, dest_path=new))
        shutil.move(fs_old, self.fs / new)

    def write(self, path: str, content: AnyStr):
        self.events.append(Event(event_type='modified', is_directory=False, src_path=path))
        p = self.fs / path
        if isinstance(content, bytes):
            p.write_bytes(content)
        elif isinstance(content, str):
            p.write_text(content)
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")
