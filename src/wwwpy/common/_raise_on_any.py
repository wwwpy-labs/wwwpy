from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Iterable


class RaiseOnAny:
    def __init__(self, payload: str | Exception | None = None, config: Config | None = None):
        if config:
            self._raise_on_any_config = config
        else:
            if payload is None:
                raise ValueError('message cannot be None')
            self._raise_on_any_config = Config(payload)

    def __getattribute__(self, name):
        return roa_get_config(self).process(name)

    def __repr__(self):
        return f'RaiseOnAny({roa_get_config(self).nested_message()})'


@dataclass
class Config:
    payload: str | Exception | None = None
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
        msg, root_config = self.nested_message(name)

        if isinstance(root_config.payload, Exception):
            raise root_config.payload

        raise Exception(msg)

    def nested_message(self, name: str | None = None) -> Tuple[str, Config]:
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
        msg = f'{c.payload} - Failures on `{name_fqn}` attribute'
        return msg, c


def roa_get_config(i: RaiseOnAny) -> Config:
    return object.__getattribute__(i, '_raise_on_any_config')


# raise_on_use

def raise_on_use(except_on: Iterable[str] = None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                x = RaiseOnAny(e)
                if except_on:
                    roa_get_config(x).accept(*except_on)
                return x

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator
