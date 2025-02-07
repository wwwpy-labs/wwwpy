from playwright.sync_api import expect

from tests import for_all_webservers
from tests.server.page_fixture import fixture, PageFixture


@for_all_webservers()
def test_sync_rpc_func(fixture: PageFixture):
    # GIVEN
    fixture.dev_mode = False
    fixture.write_module('server/rpc.py', "def func1() -> str: return 'ready'")

    # WHEN
    fixture.start_remote(  # language=python
        """
async def main():
    import js 
    from server import rpc 
    js.document.body.innerText = 'first=' + rpc.func1()
""")
    # THEN
    expect(fixture.page.locator('body')).to_have_text('first=ready', use_inner_text=True)
