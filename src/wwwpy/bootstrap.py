import textwrap
from typing import List, Tuple

from wwwpy.common import files
from wwwpy.http import HttpRoute, HttpResponse
from wwwpy.resources import build_archive, ResourceIterable

bootstrap_javascript_placeholder = '// #bootstrap-placeholder#'


def bootstrap_routes(
        resources: List[ResourceIterable],
        python: str,
        jspi=False,
        zip_route_path: str = '/wwwpy/bundle.zip',
        html: str = f'<!DOCTYPE html><h1>Loading...</h1><script>{bootstrap_javascript_placeholder}</script>',
) -> Tuple[HttpRoute, HttpRoute]:
    """Returns a tuple of two routes: (bootstrap_route, zip_route)"""

    def zip_response() -> HttpResponse:
        from itertools import chain
        zip_bytes = build_archive(chain.from_iterable(resources))
        return HttpResponse.application_zip(zip_bytes)

    zip_route = HttpRoute(zip_route_path, lambda request, resp: resp(zip_response()))
    extract_dir = files._bundle_path
    bootstrap_python = f"""
import sys
from pyodide.http import pyfetch
response = await pyfetch('{zip_route.path}')
await response.unpack_archive(extract_dir='{extract_dir}')
sys.path.insert(0, '{extract_dir}')

{python}
    """

    javascript = get_javascript_for(bootstrap_python, jspi)
    html_replaced = html.replace(bootstrap_javascript_placeholder, javascript)
    bootstrap_route = HttpRoute('/', lambda request, resp: resp(HttpResponse.text_html(html_replaced)))
    return bootstrap_route, zip_route


def get_javascript_for(python_code: str, jspi=False) -> str:
    load = '' if not jspi else '{enableRunUntilComplete: true}'
    return (_js_content
            .replace('# python replace marker', python_code)
            .replace('`# load option marker`', load))


# language=javascript
_js_content = """
if (typeof loadPyodide === 'undefined') {
    console.log('loading pyodide...');
    let script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/pyodide/v0.27.6/full/pyodide.js';
    script.onload = async () => {
        let pyodide = await loadPyodide(`# load option marker`);
        window.pyodide = pyodide;
        console.log('loading pyodide.runPythonAsync(...). See in the following lines for the code');
        console.log('-----------------------  START PYTHON CODE  -------------------------------');
        console.log(`# python replace marker`);
        console.log('-----------------------  END PYTHON CODE    -------------------------------');
        pyodide.runPythonAsync(`# python replace marker`);
    };
    document.body.append(script)
}
"""


def wrap_in_tryexcept(code: str, exception_block: str) -> str:
    """It will wrap the code in try/except and catch `Exception as exception`"""
    result = 'try:\n' + textwrap.indent(code, ' ' * 4) + '\n' + \
             'except Exception as exception:\n' + textwrap.indent(exception_block, ' ' * 4)
    return result
