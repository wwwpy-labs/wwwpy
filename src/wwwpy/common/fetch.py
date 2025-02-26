async def async_fetch_str(url: str, method: str = 'GET', data: str = '') -> str:
    pass


try:
    from wwwpy.remote.fetch import async_fetch_str
except ImportError or ModuleNotFoundError:
    from wwwpy.server.fetch import async_fetch_str
