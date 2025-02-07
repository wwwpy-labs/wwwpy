from time import sleep

from playwright.sync_api import expect

from tests import for_all_webservers
from tests.timeouts import timeout_multiplier
from tests.server.page_fixture import fixture, PageFixture
from wwwpy.common import files
from wwwpy.common.tree import print_tree


@for_all_webservers()
def test_hot_reload__modified(fixture: PageFixture):
    fixture.dev_mode = True
    fixture.start_remote("""from js import document;document.body.innerHTML = '<input id="tag1" value="ready">'""")

    expect(fixture.page.locator('id=tag1')).to_have_value('ready')

    # change server side file, should reflect on the client side
    fixture.remote_init.write_text("""import js; js.document.body.innerHTML = '<input id="tag1" value="modified">'""")
    expect(fixture.page.locator('id=tag1')).to_have_value('modified')


@for_all_webservers()
def test_hot_reload__created(fixture: PageFixture):
    fixture.dev_mode = True
    # language=python
    fixture.start_remote("""
from pathlib import Path   
from js import document, console
component1_py = Path(__file__).parent / 'component1.py'
document.body.innerHTML = f'<input id="msg1" value="exists={str(component1_py.exists())}">'
console.log(document.body.innerHTML)
console.log('importing component1')
try:
    import component1
except:
    pass 
""")
    expect(fixture.page.locator('id=msg1')).to_have_value('exists=False')

    (fixture.remote / 'component1.py').write_text(
        "import js; js.console.log('comp1!')\n" +
        """js.document.body.innerHTML = '<input id="tag1" value="import ok">'""")
    expect(fixture.page.locator('id=msg1')).to_have_value('exists=True')


@for_all_webservers()
def test_hot_reload__deleted(fixture: PageFixture):
    fixture.dev_mode = True
    fixture.remote.mkdir()
    file1 = fixture.remote / 'file1.txt'
    file1.write_text('hello')

    fixture.start_remote(
        # language=python
        """from pathlib import Path; from js import document
file1_txt = Path(__file__).parent / 'file1.txt'
document.body.innerHTML = f'<input id="msg1" value="exists={str(file1_txt.exists())}">'
""")

    expect(fixture.page.locator('id=msg1')).to_have_value('exists=True')

    file1.unlink()
    expect(fixture.page.locator('id=msg1')).to_have_value('exists=False')


@for_all_webservers()
def test_hot_reload__directory_blacklist(fixture: PageFixture):
    fixture.dev_mode = True

    fixture.start_remote(
        # language=python
        """from pathlib import Path; from js import document; import glob
rem = Path(__file__).parent
txt_list = str([str(p.relative_to(rem)) for p in rem.rglob("**/*") if p.suffix in {'.txt', '.py~'} ])
document.body.innerHTML = f'<input id="msg1" value="{txt_list}">'
""")

    expect(fixture.page.locator('id=msg1')).to_have_value("[]")

    def write_file(name: str):
        file = fixture.remote / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(f'content of {name}')

    [write_file(f'{not_ok}/f1.txt') for not_ok in files.directory_blacklist]
    write_file('not_ok/f1.py~')
    write_file('ok/f1.txt')

    expect(fixture.page.locator('id=msg1')).to_have_value("['ok/f1.txt']")

    # print_tree(fixture.tmp_path)
    # txt_list = str([str(p.relative_to(fixture.remote)) for p in fixture.remote.rglob('*.txt')])
    # print(txt_list)


class TestServerRpcHotReload:

    @for_all_webservers()
    def test_server_rpc_body_change(self, fixture: PageFixture):
        # GIVEN
        fixture.dev_mode = True
        fixture.write_module('server/rpc.py', "async def func1() -> str: return 'ready'")

        fixture.start_remote(  # language=python
            """
async def main():
    import js 
    from server import rpc 
    js.document.body.innerText = 'first=' + await rpc.func1()
""")

        expect(fixture.page.locator('body')).to_have_text('first=ready', use_inner_text=True)

        # WHEN
        fixture.write_module('server/rpc.py', "async def func1() -> str: return 'updated'")
        self._wait_filesystem_debounce_and_hotreload()
        fixture.remote_init.write_text(fixture.remote_init.read_text().replace('first=', 'second='))

        # THEN
        expect(fixture.page.locator('body')).to_have_text('second=updated', use_inner_text=True)

    @for_all_webservers()
    def test_server_rpc__call_another_file(self, fixture: PageFixture):
        # GIVEN
        fixture.dev_mode = True
        fixture.write_module('server/database.py', "conn_name = 'conn1'")
        fixture.write_module('server/rpc.py',
                             "from . import database as db\n"
                             "async def func1() -> str: res = 'conn:'+db.conn_name; print(f'res={res}\\n'); return res")

        fixture.start_remote(  # language=python
            """
async def main():
    import js 
    from server import rpc 
    js.document.body.innerText = 'first=' + await rpc.func1()
""")
        expect(fixture.page.locator('body')).to_have_text('first=conn:conn1', use_inner_text=True)

        # WHEN
        fixture.write_module('server/database.py', "conn_name = 'conn1-updated'")
        self._wait_filesystem_debounce_and_hotreload()
        # todo server/rpc should hold any request up until hotreload is finished
        fixture.remote_init.write_text(fixture.remote_init.read_text().replace('first=', 'second='))

        # THEN
        expect(fixture.page.locator('body')).to_have_text('second=conn:conn1-updated', use_inner_text=True)

    @for_all_webservers()
    def test_server_rpc_signature_change(self, fixture: PageFixture):
        # GIVEN
        fixture.dev_mode = True
        fixture.write_module('server/rpc.py', "async def func1() -> str: return 'ready'")

        fixture.start_remote(  # language=python
            """
async def main():
    import js 
    # from server import rpc # fails brutally the hotreload
    import server.rpc as rpc 
    js.document.body.innerText = 'first=' + await rpc.func1()
""")

        expect(fixture.page.locator('body')).to_have_text('first=ready', use_inner_text=True)

        # WHEN
        fixture.write_module('server/rpc.py', "async def func1(msg:str) -> str: return f'updated-{msg}'")
        fixture.remote_init.write_text(fixture.remote_init.read_text().replace(
            "'first=' + await rpc.func1()", "'second=' + await rpc.func1('new_param')"))

        # THEN
        expect(fixture.page.locator('body')).to_have_text('second=updated-new_param', use_inner_text=True)

    def _wait_filesystem_debounce_and_hotreload(self):
        # todo, awful: wait the debounce of file system events/hotreload
        sleep(0.2 * timeout_multiplier())
