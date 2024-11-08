try:
    from . import _build_meta

    __version__ = _build_meta.__version__
except:
    __version__ = 'unknown'

__all__ = ['__version__']
