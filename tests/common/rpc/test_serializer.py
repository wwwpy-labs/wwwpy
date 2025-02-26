from tests.common.rpc.test_rpc import support2_module_name
from wwwpy.common.rpc.serializer import RpcRequest


def test_rpc():
    request = RpcRequest.to_json(support2_module_name, 'support2_mul', 6, 7)
    restored = RpcRequest.from_json(request)

    assert restored.module == support2_module_name
    assert restored.func == 'support2_mul'
    assert restored.args == [6, 7]
