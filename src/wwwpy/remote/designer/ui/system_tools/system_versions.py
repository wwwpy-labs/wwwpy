import logging

import js

import wwwpy.remote.component as wpc
from wwwpy.remote.jslib import waitAnimationFrame

logger = logging.getLogger(__name__)


class SystemVersions(wpc.Component, tag_name='wwwpy-system-versions'):
    _container: js.HTMLElement = wpc.element()
    _wwwpy: js.HTMLElement = wpc.element()
    _python_remote: js.HTMLElement = wpc.element()
    _python_server: js.HTMLElement = wpc.element()
    _pyodide: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
        <pre data-name="_container">
    <span data-name="_wwwpy">wwwpy==...</span>
    <span data-name="_pyodide">pyodide==...</span>
    
    Python versions:
    <span data-name="_python_remote">pyton remote==...</span>
    <span data-name="_python_server">pyton server==...</span>
</pre>"""

    async def after_init_component(self):
        await waitAnimationFrame()

        import platform
        pyver = platform.python_version()

        try:
            import wwwpy
            wp_ver = wwwpy.__version__
        except Exception as e:
            wp_ver = e.message

        try:
            import js
            pyodide_ver = js.window.pyodide.version
        except Exception as e:
            pyodide_ver = e.message

        self._wwwpy.innerText = f'wwwpy==' + wp_ver
        self._pyodide.innerText = 'pyodide==' + pyodide_ver
        self._python_remote.innerText = 'remote==' + pyver + ' (this is tied to Pyodide version)'

        from wwwpy.server.designer import rpc
        server_version = await rpc.server_python_version_string()
        self._python_server.innerText = 'server==' + server_version
