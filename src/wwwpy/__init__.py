try:
    from . import _build_meta

    __version__ = _build_meta.__version__
    __banner__ = f'wwwpy v{__version__}'
except:
    __version__ = 'unknown'
    __banner__ = 'wwwpy version unknown'

__all__ = ['__version__']
