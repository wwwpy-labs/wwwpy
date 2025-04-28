from wwwpy.common.exitlib import on_exit


def test_on_exit_callback_triggered():
    calls = []

    def fun():
        on_exit(lambda: calls.append(1))

    fun()

    assert calls == [1]


def test_multiple_on_exit_callbacks():
    calls = []

    def fun():
        on_exit(lambda: calls.append(1))
        on_exit(lambda: calls.append(2))

    fun()

    assert calls == [1, 2]


def test_exception_on_exit():
    calls = []

    def fun():
        on_exit(lambda: calls.append(1))
        raise Exception("Test exception")

    try:
        fun()
    except Exception:
        pass

    assert calls == [1]
