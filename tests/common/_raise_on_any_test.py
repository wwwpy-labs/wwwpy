import pytest

from wwwpy.common._raise_on_any import RaiseOnAny, roa_get_config, raise_on_use


def test_throw_on_any_access_and_call():
    msg = 'Some message 123'
    x = RaiseOnAny(msg)
    with pytest.raises(Exception) as excinfo1:
        x.some()
    assert msg in str(excinfo1.value)

    with pytest.raises(Exception) as excinfo2:
        _ = x.attr1
    assert msg in str(excinfo2.value)

    with pytest.raises(Exception) as excinfo3:
        x.anything()
    assert msg in str(excinfo3.value)


def test_accept_should_notRaise():
    x = RaiseOnAny('msg1')
    roa_get_config(x).accept('attr1')

    attr1 = x.attr1  # noqa


def test_accept_should_return_RaiseOnAny():
    x = RaiseOnAny('msg1')
    roa_get_config(x).accept('attr1')

    attr1 = x.attr1

    assert isinstance(attr1, RaiseOnAny)

    with pytest.raises(Exception):
        attr1.some()


def test_accept_give_nice_message():
    x = RaiseOnAny('msg1')
    roa_get_config(x).accept('attr1')

    with pytest.raises(Exception) as excinfo:
        x.attr1.some()

    s = str(excinfo.value)
    assert 'msg1' in s
    assert 'attr1.some' in s


def test_accept_multiple():
    x = RaiseOnAny('msg1')
    roa_get_config(x).accept('attr1', 'attr2')

    a1 = x.attr1
    a2 = x.attr2


def test_str():
    x = RaiseOnAny('msg1')

    s = str(x)
    assert 'msg1' in s


def test_str_nested():
    x = RaiseOnAny('msg1')
    roa_get_config(x).accept('attr1')
    s = str(x.attr1)

    assert 'msg1' in s
    assert 'attr1' in s

    r = repr(x.attr1)
    assert 'msg1' in r
    assert 'attr1' in r


class Test_raise_on_use:

    def test_should_pass_through_if_no_exception(self):
        @raise_on_use()
        def f():
            return 1

        assert 1 == f()
        assert f.__name__ == 'f'

    def test_should_raise_if_exception__when_used(self):
        @raise_on_use()
        def f():
            raise ValueError('Some test error')

        result = f()  # should be ok

        with pytest.raises(Exception) as excinfo:
            result.anything()
