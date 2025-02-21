from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    name: str
    version: str


@dataclass(frozen=True)
class PackageSpecification:
    name: str
    version_specs: str | None = None
    """Version specifications for the package or None for any version. E.g. '==1.0.0' or '>=1.0.0'
        
    See https://packaging.python.org/en/latest/specifications/version-specifiers/
    """

    def build_installation_string(self) -> list[str]:
        if self.version_specs is None:
            return [self.name]
        return [f"{self.name}{self.version_specs}"]


@dataclass(frozen=True)
class PackageRequest:
    install: list[PackageSpecification]
