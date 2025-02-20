def is_pyodide() -> bool:
    try:
        import pyodide
        return True
    except ImportError:
        return False
