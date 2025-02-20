from __future__ import annotations
import asyncio
import importlib.metadata

from wwwpy.common.designer.packaging.packages import Package, PackageSpecification
from wwwpy.common.result import Result


class PackageManager:

    def installed_packages(self) -> list[Package]:
        packages = []
        unique = set()
        for dist in importlib.metadata.distributions():
            package = Package(name=dist.metadata['Name'], version=dist.version)
            if package not in unique:
                unique.add(package)
                packages.append(package)

        return packages

    async def install_package(self, specification: PackageSpecification) -> Result[None, Exception]:
        ...

    # def update_package(self, specification: PackageSpecification) -> Result[None, Exception]: ...

    # def uninstall_package(self, package: Package) -> Result[None, Exception]: ...

    # def reload_packages(self) -> Result[list[Package], Exception]: ...


class PipPackageManager(PackageManager):
    """Pip package manager, using pip as a module, not with subprocess"""

    async def install_package(self, specification: PackageSpecification) -> Result[None, Exception]:
        try:
            import pip
            pip.main(['install', specification.build_installation_string()])
            return Result.success(None)
        except Exception as e:
            return Result.failure(e)


class UvPackageManager(PackageManager):

    async def install_package(self, specification: PackageSpecification) -> Result[None, Exception]:
        try:
            arg = specification.build_installation_string()
            cmd = ["uv", "pip", "install"] + arg
            proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                        stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                return Result.success(None)
            return Result.failure(
                Exception(f"uv pip install failed with exit code {proc.returncode}: {stderr.decode()}"))
        except Exception as e:
            return Result.failure(e)
