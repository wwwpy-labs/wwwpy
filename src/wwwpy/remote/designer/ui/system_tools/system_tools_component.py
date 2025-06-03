import logging

import js

import wwwpy.remote.component as wpc

logger = logging.getLogger(__name__)


class SystemToolsComponent(wpc.Component, tag_name='wwwpy-system-tools'):
    _explore_fs: js.HTMLElement = wpc.element()
    _logger_levels: js.HTMLElement = wpc.element()
    _python_console: js.HTMLButtonElement = wpc.element()
    _system_versions: js.HTMLButtonElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div style='display: inline-flex; flex-direction: column; gap: 5px' >        
<button data-name="_explore_fs">Explore Filesystem</button>
<button data-name="_logger_levels">Logger Levels</button>
<button data-name="_python_console">Python Console</button>
<button data-name="_system_versions">System Versions</button>
</div>
"""

    async def _explore_fs__click(self, event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        from wwwpy.remote.designer.ui import filesystem_tree
        filesystem_tree.show_explorer(DevModeComponent.instance.root_element())

    async def _logger_levels__click(self, event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        from wwwpy.remote.designer.ui.window_component import new_window
        w1 = new_window('Logger levels')

        from wwwpy.remote.designer.ui.system_tools.logger_levels import LoggerLevelsComponent
        w1.element.append(LoggerLevelsComponent().element)
        DevModeComponent.instance.root_element().append(w1.element)

    async def _python_console__click(self, event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        from wwwpy.remote.designer.ui.window_component import new_window
        w1 = new_window('Python console')
        from wwwpy.remote.designer.ui.python_console import PythonConsoleComponent
        w1.element.append(PythonConsoleComponent().element)
        DevModeComponent.instance.root_element().append(w1.element)

    async def _system_versions__click(self, event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        from wwwpy.remote.designer.ui.system_tools.system_versions import SystemVersions
        DevModeComponent.instance.show_window('Show System Versions', SystemVersions())
