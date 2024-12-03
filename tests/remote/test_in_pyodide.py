import pytest
from js import document


def test_first():
    document.body.innerHTML = '<input id="tag1" value="foo1">'
    assert document.getElementById('tag1').value == 'foo1'


@pytest.mark.asyncio
async def test_second():
    return
    assert False, 'This sadly succeeds, because async tests are running correctly in Pyodide' + \
        'See issue: https://github.com/pyodide/pyodide/issues/2221#issuecomment-2379624269'
