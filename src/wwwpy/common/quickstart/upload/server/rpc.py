import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


async def upload_init(name: str, size: int):
    file = _resolve_file(name)
    file.unlink(missing_ok=True)
    file.touch()
    logger.info(f'upload_init name={name} size={size}')
    return None


async def upload_append(name: str, b64str: str):
    logger.info(f'upload_append name={name} len(b64str)={len(b64str)}')
    file = _resolve_file(name)
    bytes_append = base64.b64decode(b64str)
    with file.open('ab') as f:
        f.write(bytes_append)
    return None


async def upload_abort(name: str):
    logger.info(f'upload_abort name={name}')
    file = _resolve_file(name)
    file.unlink(missing_ok=True)
    return None


def _resolve_file(name: str) -> Path:
    folder = Path(__file__).parent.parent / 'uploads'
    candidate = folder / name
    # security check: candidate is inside the folder?
    if not candidate.resolve().is_relative_to(folder.resolve()):
        raise ValueError(f'Invalid path: {candidate}')
    candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate
