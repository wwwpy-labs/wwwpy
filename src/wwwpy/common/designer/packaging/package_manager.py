from __future__ import annotations

import asyncio
import configparser
import importlib.metadata
import sys
from pathlib import Path
from typing import Tuple

from wwwpy.common.designer.packaging.packages import Package, PackageSpecification
from wwwpy.common.result import Result


class PackageManager:

    async def installed_packages(self) -> Result[list[Package], Exception]:
        try:
            return Result.success(self._installed_packages_sync())
        except Exception as e:
            return Result.failure(e)

    def _installed_packages_sync(self) -> list[Package]:
        packages = []
        unique = set()
        for dist in importlib.metadata.distributions():
            package = Package(name=dist.metadata['Name'], version=dist.version)
            if package not in unique:
                unique.add(package)
                packages.append(package)

        return packages

    async def _install_package(self, specification: PackageSpecification) -> Exception | None:
        raise NotImplementedError()

    async def install_package_list(self, specifications: list[PackageSpecification | str]) -> Tuple[
        list[Package], Exception | None]:
        """Install all specified packages, stop on the first error"""
        packages = []
        for spec in specifications:
            result = await self.install_package(spec)
            if result.is_failure:
                return packages, result.error_or_null()
            packages.append(Package(name=spec.name, version=''))
        return packages, None

    async def install_package(self, specification: PackageSpecification | str) -> Exception | None:
        spec = PackageSpecification(specification) if isinstance(specification, str) else specification
        return await self._install_package(spec)

    # def update_package(self, specification: PackageSpecification) -> Result[None, Exception]: ...

    async def uninstall_package(self, package: Package | str) -> Exception | None:
        raise NotImplementedError()

    # def reload_packages(self) -> Result[list[Package], Exception]: ...


class PipPackageManager(PackageManager):
    """Pip package manager, using pip as a module, not with subprocess"""

    async def _install_package(self, specification: PackageSpecification) -> Exception | None:
        save_argv = sys.argv
        save_exit = sys.exit
        exit_args = []

        def _sys_exit(arg0):
            exit_args.append(arg0)

        sys.exit = _sys_exit
        try:
            import runpy
            sys.argv = ['pip', 'install'] + specification.build_installation_string()
            runpy.run_module("pip", run_name="__main__")
            if exit_args and exit_args[0] == 0:
                return None
            return Exception(f"pip install failed with exit code {exit_args}")
        except Exception as e:
            return e
        finally:
            sys.argv = save_argv
            sys.exit = save_exit


class UvPackageManager(PackageManager):

    async def _install_package(self, specification: PackageSpecification) -> Exception | None:
        try:
            arg = specification.build_installation_string()
            cmd = ["uv", "pip", "install"] + arg
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                return None
            return Exception(f"uv pip install failed with exit code {proc.returncode}: {stderr.decode()}")
        except Exception as e:
            return e

    async def uninstall_package(self, package: Package | str) -> Exception | None:
        try:
            package_name = package.name if isinstance(package, Package) else package
            cmd = ["uv", "pip", "uninstall", package_name]
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                return None
            return Exception(f"uv pip uninstall failed with exit code {proc.returncode}: {stderr.decode()}")
        except Exception as e:
            return e


class MicropipPackageManager(PackageManager):
    async def _install_package(self, specification: PackageSpecification) -> Exception | None:
        try:
            import micropip
            await micropip.install(specification.build_installation_string())
            return None
        except Exception as e:
            return e

    async def uninstall_package(self, package: Package | str) -> Exception | None:
        try:
            package_name = package.name if isinstance(package, Package) else package
            import micropip
            await micropip.uninstall(package_name)
        except Exception as e:
            return e
def guess_package_manager() -> PackageManager:
    return guess_package_manager_class().get_or_throw()()


def guess_package_manager_class() -> Result[type[PackageManager], ExceptionGroup[...]]:
    exceptions = []
    try:
        import pip
        return Result.success(PipPackageManager)
    except Exception as e:
        exceptions.append(e)

    try:
        import micropip
        return Result.success(MicropipPackageManager)
    except Exception as e:
        exceptions.append(e)

    try:
        _is_uv_managed()
        return Result.success(UvPackageManager)
    except Exception as e:
        exceptions.append(e)

    return Result.failure(ExceptionGroup(*exceptions))


def _is_uv_managed():
    cfg_path = Path(sys.prefix) / 'pyenv.cfg'
    if not cfg_path.is_file():
        return False

    content = "[dummy]\n" + cfg_path.read_text()
    config = configparser.ConfigParser()
    config.read_string(content)

    return 'uv' in config['dummy']
