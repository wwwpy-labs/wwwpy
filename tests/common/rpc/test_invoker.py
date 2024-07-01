from tests.common.rpc.test_rpc import support2_module_name
from wwwpy.common.rpc.ast_parser import module_from_package_name
from wwwpy.common.rpc.invoker import Invoker


def test_simple_invoke():
    module = module_from_package_name(support2_module_name)
    target = Invoker(module)
    # THEN
    actual = target['support2_mul'].func(6, 7)
    assert actual == 42

