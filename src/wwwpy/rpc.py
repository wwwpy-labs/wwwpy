from __future__ import annotations

import importlib
import logging
import tempfile
import traceback
from inspect import getmembers, isfunction, signature, iscoroutinefunction, Signature
from pathlib import Path
from types import ModuleType, FunctionType
from typing import NamedTuple, List, Tuple, Optional, Callable

from wwwpy.common import modlib
from wwwpy.common.asynclib import OptionalCoroutine
from wwwpy.common.http_transport import ServerHttpTransport, RemoteHttpTransport
from wwwpy.common.rpc.hibrid_dispatcher import HybridDispatcher
from wwwpy.common.rpc.serializer import RpcRequest, RpcResponse
from wwwpy.common.rpc.v2.caller_proxy import caller_proxy_generate
from wwwpy.common.rpc2.default_skeleton import DefaultSkeleton
from wwwpy.common.rpc2.default_stub import DefaultStub
from wwwpy.common.rpc2.encoder_decoder import JsonEncoderDecoder
from wwwpy.common.rpc2.stub import generate_stub
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


class RpcRoute:
    def __init__(self, route_path: str):
        self._allowed_modules: set[str] = set()
        self.route = HttpRoute(route_path, self._route_callback)
        self.tmp_bundle_folder = Path(tempfile.mkdtemp())

    def _route_callback(self, request: HttpRequest,
                        resp_callback: Callable[[HttpResponse], OptionalCoroutine]) -> OptionalCoroutine:

        request_content = request.content.decode('utf-8')
        transport = ServerHttpTransport(request_content)
        encdec = JsonEncoderDecoder()
        skeleton = DefaultSkeleton(transport, encdec, self._allowed_modules)

        skeleton.invoke_tobe_fixed()

        if transport.response is None:
            raise Exception('No response was provided')

        response = HttpResponse(transport.response, 'text/plain')
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

    # todo could be called invoke or call_site_invoke or server_dispatch (but server is charged maybe brainstorm a name)
    #  in the rpc realm how is it called the caller and the called?
    def callee_dispatch(self, request: str) -> str:
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
            module_source = module.path.read_text()
            sub_imports = '\n'.join(_make_import(o) for o in [RemoteHttpTransport, JsonEncoderDecoder]) + '\n'
            stub_args = (f'{RemoteHttpTransport.__name__}("{self.route.path}"), ' +
                         f'{JsonEncoderDecoder.__name__}(), __name__')
            stub_source = sub_imports + generate_stub(module_source, DefaultStub, stub_args)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(stub_source)
            logger.debug(f'Module `{module_name}` len(stub_source)={len(stub_source)}')
            add.append(file)
        return add, rem


def generate_stub_source(module: SourceModule, rpc_url: str) -> str:
    imports = 'from wwwpy.common.fetch import async_fetch_str'
    proxy_args = f'"{module.name}", "{rpc_url}"'
    gen = caller_proxy_generate(module.source(), HybridDispatcher, proxy_args)
    gen = imports + '\n\n' + gen
    return gen


def _make_import(obj: any) -> str:
    return f'from {obj.__module__} import {obj.__name__}'
