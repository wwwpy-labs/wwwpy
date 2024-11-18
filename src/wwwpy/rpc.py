import tempfile
import traceback
from inspect import getmembers, isfunction, signature, iscoroutinefunction, Signature
from types import ModuleType, FunctionType
from typing import NamedTuple, List, Tuple, Any, Optional, Callable, Awaitable, Protocol, Iterator

from wwwpy.common import modlib
from wwwpy.common.iterlib import CallableToIterable
from wwwpy.common.rpc.serializer import RpcRequest, RpcResponse
from wwwpy.exceptions import RemoteException
from wwwpy.http import HttpRoute, HttpResponse, HttpRequest
from wwwpy.resources import Resource, StringResource, ResourceIterable, from_directory
from wwwpy.unasync import unasync
from pathlib import Path


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


class Proxy:
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

    def _route_callback(self, request: HttpRequest) -> HttpResponse:
        resp = self.dispatch(request.content)
        response = HttpResponse(resp, 'application/json')
        return response

    def add_module(self, module_name: str):
        # todo rename to `allow`
        if not isinstance(module_name, str):
            raise TypeError('module_name must be a string')
        self._allowed_modules.add(module_name)

    def find_module(self, module_name: str) -> Optional[Module]:
        if module_name not in self._allowed_modules:
            return None
        if modlib._find_module_path(module_name) is None:
            return None
        import importlib
        module = importlib.import_module(module_name)
        # todo, cache? beware of hot reload
        return Module(module)

    def dispatch(self, request: str) -> str:
        rpc_request = RpcRequest.from_json(request)
        # print(f'dispatch req={request}')
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

    def generate_remote_stubs(self) -> List[Path]:
        result = []
        for module_name in self._allowed_modules:
            module = self.find_module(module_name)
            if module is None:
                continue
            imports = 'from wwwpy.remote.fetch import async_fetch_str'
            stub_source = generate_stub_source(module, self.route.path, imports)
            filename = module_name.replace('.', '/') + '.py'
            file = self.tmp_bundle_folder / filename
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(stub_source)
            result.append(file)
        return result


def generate_stub_source(module: Module, rpc_url: str, imports: str):
    module_name = module.name
    # language=python
    stub_header = f"""
from __future__ import annotations
from wwwpy.rpc import Proxy
{imports}

rpc_url = '{rpc_url}'
module_name = '{module_name}'
proxy = Proxy(module_name, rpc_url, async_fetch_str)
    """

    stub_functions = ''
    for f in module.functions:
        if f.name.startswith('_'):
            continue
        parameters = f.sign.parameters.values()
        params_list = ', '.join(p.name for p in parameters)
        args_list = '' if params_list == '' else ', ' + params_list
        fun_stub_as = f'\nasync def {f.name}{f.signature}:\n' + \
                      f'    return await proxy.dispatch_async("{f.name}"{args_list})\n'
        fun_stub_sy = f'\ndef {f.name}{f.signature}:\n' + \
                      f'    return proxy.dispatch_sync("{f.name}"{args_list})\n'
        stub_functions += fun_stub_as if f.is_coroutine_function else fun_stub_sy

    return stub_header + stub_functions
