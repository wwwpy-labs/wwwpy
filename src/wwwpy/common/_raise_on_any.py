class RaiseOnAny:
    def __init__(self, message):
        self._message = message

    def __getattribute__(self, name):
        m = object.__getattribute__(self, '_message')
        if name == '_message':
            return m
        raise Exception(m)
