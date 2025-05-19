from __future__ import annotations

from dataclasses import dataclass, field


class RaiseOnAny:
    def __init__(self, message: str | None = None, config: Config | None = None):
        if config:
            self._raise_on_any_config = config
        else:
            if message is None:
                raise ValueError('message cannot be None')
            self._raise_on_any_config = Config(message)

    def __getattribute__(self, name):
        return roa_get_config(self).process(name)

    def __repr__(self):
        return f'RaiseOnAny({roa_get_config(self).nested_message()})'


@dataclass
class Config:
    message: str | None = None
    parent: Config | None = None
    sub_attr: str = 'self'
    accept_set: set[str] = field(default_factory=set)

    def accept(self, *name: str):
        for n in name:
            self.accept_set.add(n)

    def nested(self, name: str) -> RaiseOnAny | None:
        if name in self.accept_set:
            return RaiseOnAny(config=Config(None, self, name))
        return None

    def process(self, name):
        n = self.nested(name)
        if n:
            return n
        msg = self.nested_message(name)
        raise Exception(msg)

    def nested_message(self, name: str | None = None) -> str:
        attrs = []
        c = self
        while True:
            attrs.insert(0, c.sub_attr)
            if c.parent:
                c = c.parent
            else:
                break

        if name:
            attrs.append(name)
        name_fqn = '.'.join(attrs)
        msg = f'{c.message} - Failures on `{name_fqn}` attribute'
        return msg


def roa_get_config(i: RaiseOnAny) -> Config:
    return object.__getattribute__(i, '_raise_on_any_config')


# raise_on_use

def raise_on_use():
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return RaiseOnAny(str(e))

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator
