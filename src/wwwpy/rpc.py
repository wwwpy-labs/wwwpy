from __future__ import annotations

import importlib
import logging
import tempfile
import traceback
from inspect import getmembers, isfunction, signature, iscoroutinefunction, Signature
from pathlib import Path
from types import ModuleType, FunctionType
from typing import NamedTuple, List, Tuple, Any, Optional, Callable, Awaitable, Protocol

from wwwpy.common import modlib
from wwwpy.common.asynclib import OptionalCoroutine
from wwwpy.common.rpc.serializer import RpcRequest, RpcResponse
from wwwpy.common.rpc.v2 import proxy_generator
from wwwpy.common.rpc.v2.dispatcher import Dispatcher
from wwwpy.exceptions import RemoteException
from wwwpy.http import HttpRoute, HttpResponse, HttpRequest
from wwwpy.resources import ResourceIterable, from_directory
from wwwpy.unasync import unasync

logger = logging.getLogger(__name__)


class Function(NamedTuple):
    name: str
    func: FunctionType
    signature: str
    is_coroutine_function: bool
    sign: Signature
    blocking: FunctionType


def _std_function_to_function(fun_tuple: Tuple[str, FunctionType]) -> Function:
    name = fun_tuple[0]
    func = fun_tuple[1]
    sign = signature(func)
    is_coroutine_function = iscoroutinefunction(func)
    blocking = unasync(func)
    return Function(name, func, str(sign), is_coroutine_function, signature(func), blocking)


class SourceModule:
    def __init__(self, path: Path | str, module_name: str):
        self.path = Path(path)
        self.name = module_name

    def source(self) -> str:
        return self.path.read_text()


class Module:
    def __init__(self, module: ModuleType):
        self.module = module
        self.name = module.__name__

        self.functions: List[Function] = function_list(self.module)
        self._funcs = {f.name: f for f in self.functions}

    def __getitem__(self, name) -> Function:
        return self._funcs.get(name, None)


def function_list(module: ModuleType) -> List[Function]:
    return list(map(_std_function_to_function, getmembers(module, isfunction)))


Fetch = Callable[[str, str, str], Awaitable[str]]


class Fetch(Protocol):
    def __call__(self, url: str, method: str = '', data: str = '') -> Awaitable[str]: ...


class Proxy(Dispatcher):
    def __init__(self, module_name: str, rpc_url: str, fetch: Fetch):
        self.rpc_url = rpc_url
        self.fetch = fetch
        self.module_name = module_name

    async def dispatch_async(self, func_name: str, *args) -> Any:
        rpc_request = RpcRequest.build_request(self.module_name, func_name, *args)
        json_response = await self.fetch(self.rpc_url, method='POST', data=rpc_request.json())
        response = RpcResponse.from_json(json_response)
        ex = response.exception
        if ex is not None and ex != '':
            raise RemoteException(ex)
        return response.result

    def dispatch_sync(self, func_name: str, *args) -> Any:
        rpc_request = RpcRequest.build_request(self.module_name, func_name, *args)
        import js
        xhr = js.XMLHttpRequest.new()
        xhr.open('POST', self.rpc_url, False)
        xhr.setRequestHeader('Content-Type', 'application/json')
        xhr.send(rpc_request.json())
        json_response = xhr.responseText
        response = RpcResponse.from_json(json_response)
        ex = response.exception
        if ex is not None and ex != '':
            raise RemoteException(ex)
        return response.result


class RpcRoute:
    def __init__(self, route_path: str):
        self._allowed_modules: set[str] = set()
        self.route = HttpRoute(route_path, self._route_callback)
        self.tmp_bundle_folder = Path(tempfile.mkdtemp())

    def _route_callback(self, request: HttpRequest,
                        resp_callback: Callable[[HttpResponse], OptionalCoroutine]) -> OptionalCoroutine:
        resp = self.dispatch(request.content)
        response = HttpResponse(resp, 'application/json')
        return resp_callback(response)

    def allow(self, module_name: str):
        if not isinstance(module_name, str):
            raise TypeError('module_name must be a string')
        self._allowed_modules.add(module_name)

    def find_module(self, module_name: str) -> Optional[Module]:
        if module_name not in self._allowed_modules:
            return None
        if modlib._find_module_path(module_name) is None:
            return None
        try:
            module = importlib.import_module(module_name)
        except Exception:
            logger.exception(f'Cannot import module {module_name} even though find_module_path found it')
            return None

        # todo, cache? beware of hot reload
        return Module(module)

    def find_source_module(self, module_name: str) -> Optional[SourceModule]:
        if module_name not in self._allowed_modules:
            return None
        path = modlib._find_module_path(module_name)
        if path is None:
            return None
        try:
            module = SourceModule(path, module_name)
            return module
        except Exception:
            logger.exception(f'Cannot import module {module_name} even though find_module_path found it')
            return None

    def dispatch(self, request: str) -> str:
        rpc_request = RpcRequest.from_json(request)

        module = self.find_module(rpc_request.module)
        function = module[rpc_request.func]
        exception = ''
        result = None
        try:
            result = function.blocking(*rpc_request.args)
        except Exception:
            exception = traceback.format_exc()

        response = RpcResponse(result, exception)
        return response.to_json()

    def remote_stub_resources(self) -> ResourceIterable:
        return from_directory(self.tmp_bundle_folder)

    def generate_remote_stubs(self) -> tuple[List[Path], List[Path]]:
        logger.debug(f'generate_remote_stubs in {self.tmp_bundle_folder}')
        add = []
        rem = []
        for module_name in self._allowed_modules:
            module = self.find_source_module(module_name)
            filename = module_name.replace('.', '/') + '.py'
            file = self.tmp_bundle_folder / filename
            if module is None:
                if file.exists():
                    file.unlink(missing_ok=True)
                    rem.append(file)
                continue
            imports = 'from wwwpy.remote.fetch import async_fetch_str'
            stub_source = generate_stub_source(module, self.route.path, imports)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(stub_source)
            logger.debug(f'Module `{module_name}` len(stub_source)={len(stub_source)}')
            add.append(file)
        return add, rem


def generate_stub_source(module: SourceModule, rpc_url: str, imports: str) -> str:
    proxy_args = f'"{module.name}", "{rpc_url}", async_fetch_str'
    gen = proxy_generator.generate(module.source(), Proxy, proxy_args)
    gen = imports + '\n\n' + gen
    return gen
