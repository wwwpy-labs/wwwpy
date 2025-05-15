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


@dataclass
class Config:
    message: str
    parent: Config | None = None
    sub_attr: str = 'self'
    accept_set: set[str] = field(default_factory=set)

    def accept(self, *name: str):
        for n in name:
            self.accept_set.add(n)

    def nested(self, name: str) -> RaiseOnAny | None:
        if name in self.accept_set:
            return RaiseOnAny(config=Config(self.message, self, name))
        return None

    def process(self, name):
        n = self.nested(name)
        if n:
            return n

        attrs = []
        c = self
        while c:
            attrs.insert(0, c.sub_attr)
            c = c.parent
        attrs.append(name)
        name_fqn = '.'.join(attrs)
        msg = f'{self.message} - Failed on `{name_fqn}` attribute'
        raise Exception(msg)


def roa_get_config(i: RaiseOnAny) -> Config:
    return object.__getattribute__(i, '_raise_on_any_config')
