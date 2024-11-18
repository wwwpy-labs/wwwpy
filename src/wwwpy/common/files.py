from __future__ import annotations
# todo rename to filelib.py; reading files.something is confusing
import hashlib
import os
import zipfile
from io import BytesIO
from pathlib import Path

# todo move to different module; these are application constants but below we have general purpose functions
directory_blacklist = {'.mypy_cache', '__pycache__', '.DS_Store'}
extension_blacklist = {'.py~'}
_bundle_path = '/wwwpy_bundle'


def _zip_path(zip_file, path):
    path = str(path)
    for root, dirs, files in os.walk(path):
        for file in files:
            zip_file.write(os.path.join(root, file),
                           os.path.relpath(os.path.join(root, file),
                                           os.path.join(path, '../remote')))


def zip_in_memory(path):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zip_file:
        _zip_path(zip_file, path)

    stream.seek(0)
    return stream.getbuffer().tobytes()


def get_all_paths_with_hashes(path: str | Path) -> set[tuple[str, str | None]]:
    path = Path(path)
    paths = set()
    for path in path.rglob('*'):
        relative_path = path.relative_to(path)
        if path.is_file():
            file_hash = get_file_hash(path)
            paths.add((str(relative_path), file_hash))
        else:
            paths.add((str(relative_path), None))  # Directories don't need a hash
    return paths


def get_file_hash(filepath: str | Path) -> str:
    hash_sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


import gzip
import io
import base64


def bytes_gzip(content: bytes) -> bytes:
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
        gz_file.write(content)
    return buffer.getvalue()


def bytes_ungzip(compressed_data: bytes) -> bytes:
    buffer = io.BytesIO(compressed_data)
    with gzip.GzipFile(fileobj=buffer, mode='rb') as gz_file:
        return gz_file.read()


def str_gzip(content: str) -> bytes:
    return bytes_gzip(content.encode('utf-8'))


def str_ungzip(compressed_data: bytes) -> str:
    return bytes_ungzip(compressed_data).decode('utf-8')


def str_gzip_base64(content: str) -> str:
    """
    Compresses a string using gzip and encodes it with Base64.

    :param content: The input string to compress and encode.
    :return: A Base64-encoded string of the compressed data.
    """
    compressed_bytes = str_gzip(content)
    base64_encoded = base64.b64encode(compressed_bytes).decode('utf-8')
    return base64_encoded


def str_ungzip_base64(base64_string: str) -> str:
    """
    Decodes a Base64-encoded string and decompresses it using gzip.

    :param base64_string: The Base64-encoded compressed string.
    :return: The original uncompressed string.
    """
    compressed_bytes = base64.b64decode(base64_string)
    decompressed_str = str_ungzip(compressed_bytes)
    return decompressed_str
