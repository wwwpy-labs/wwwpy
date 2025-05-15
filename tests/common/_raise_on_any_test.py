import pytest

from wwwpy.common._raise_on_any import RaiseOnAny


def test_throw_on_any_access_and_call():
    msg = 'This is not yet implemented'
    x = RaiseOnAny(msg)
    with pytest.raises(Exception) as excinfo1:
        x.some()
    assert str(excinfo1.value) == msg
    with pytest.raises(Exception) as excinfo2:
        _ = x.attr1
    assert str(excinfo2.value) == msg
    with pytest.raises(Exception) as excinfo3:
        x.anything()
    assert str(excinfo3.value) == msg
