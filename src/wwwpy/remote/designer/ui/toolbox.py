from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from functools import partial
from typing import Optional, Tuple, List

import js
from js import document, console, Event, HTMLElement, window
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.common import state, modlib
from wwwpy.common.designer import element_library
from wwwpy.common.designer.canvas_selection import CanvasSelection, CanvasSelectionChangeEvent
from wwwpy.common.designer.code_edit import add_element, AddResult, AddFailed
from wwwpy.common.designer.element_library import Help, ElementDef
from wwwpy.common.designer.html_edit import Position
from wwwpy.common.designer.html_locator import path_to_index
from wwwpy.common.designer.locator_lib import Locator
from wwwpy.common.injectorlib import inject
from wwwpy.remote import dict_to_js
from wwwpy.remote.designer.drop_zone import DropZone, DropZoneHover
from wwwpy.remote.designer.global_interceptor import GlobalInterceptor, InterceptorEvent
from wwwpy.remote.designer.helpers import _element_lbl, _help_button, info_link, _help_url
from wwwpy.remote.designer.ui.property_editor import PropertyEditor
from wwwpy.remote.designer.ui.window_component import WindowComponent
from wwwpy.remote.designer.ui.window_component import new_window, Geometry
from wwwpy.server.designer import rpc
from . import filesystem_tree
from .help_icon import HelpIcon  # noqa
from .mailto_component import MailtoComponent
from .system_tools.logger_levels import LoggerLevelsComponent
from ..locator_js import locator_from

logger = logging.getLogger(__name__)


@dataclass
class ToolboxState:
    geometry: Tuple[int, int, int, int] = field(default=(30, 200, 400, 330))
    toolbox_search: str = ''
    selected_element_path: Optional[Locator] = None


@dataclass
class MenuMeta:
    label: str
    html: str
    always_visible: bool = False
    p_element: js.HTMLElement = None
    help: Help = None


def menu(label, always_visible=False):
    def wrapped(fn, label=label):
        help = None
        if isinstance(label, Help):
            help = label
            label = label.description
        fn.label = label
        fn.meta = MenuMeta(label, label, always_visible, help=help)
        return fn

    return wrapped


class ToolboxComponent(wpc.Component, tag_name='wwwpy-toolbox'):
    _title: js.HTMLDivElement = wpc.element()
    body: HTMLElement = wpc.element()
    inputSearch: js.HTMLInputElement = wpc.element()
    _window: WindowComponent = wpc.element()
    property_editor: PropertyEditor = wpc.element()
    _select_element_btn: js.HTMLElement = wpc.element()
    _select_clear_btn: js.HTMLElement = wpc.element()
    components_marker = '-components-'
    _toolbox_state: ToolboxState = None
    _canvas_selection: CanvasSelection = inject()

    @property
    def visible(self) -> bool:
        return self._window.element.style.display != 'none'

    @visible.setter
    def visible(self, value: bool):
        self._window.element.style.display = 'block' if value else 'none'

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>
.two-column-layout {
  display: flex;
  flex-wrap: wrap;
}

.two-column-layout p {
  width: calc(50% - 10px); /* 50% width minus half of the gap */
  margin: 0 20px 10px 0; /* Right margin creates gap between columns */
}

.two-column-layout p:nth-child(even) {
  margin-right: 0; /* Removes right margin for every even child */
}
</style>     
<wwwpy-window data-name='_window'>
    <div slot='title' data-name="_title" style='text-align: center'></div>
    <div  style="text-align: center; padding: 8px">     
        <button data-name="_select_element_btn">Select element...</button>   
        <button data-name="_select_clear_btn">Clear selection</button>   
        <wwwpy-property-editor data-name="property_editor"></wwwpy-property-editor>        
        <p><input data-name='inputSearch' type='search' placeholder='type to filter...'></p>
        <div data-name='body' class='two-column-layout'></div>
    </div>   
</wwwpy-window>         
"""
        import wwwpy
        self._title.innerText = f'toolbox - {wwwpy.__banner__}'

        def _csce(event: CanvasSelectionChangeEvent):
            logger.debug(f'canvas selection changed: {event}')
            self._toolbox_state.selected_element_path = event.new
            self._restore_selected_element_path()

        self._canvas_selection.on_change.add(_csce)

    def connectedCallback(self):
        self._manage_toolbox_state()
        self._window.closable = False
        attrs = [v for k, v in vars(self.__class__).items() if hasattr(v, 'label')]
        self._all_items: List[MenuMeta] = []

        def add_p(menu_meta: MenuMeta, callback):  # callback can be async
            self._all_items.append(menu_meta)
            p: js.HTMLElement = document.createElement('p')
            p.style.color = 'white'
            menu_meta.p_element = p
            p.innerHTML = menu_meta.html
            p.addEventListener('click', create_proxy(callback))

        def add_comp(element_def: ElementDef):

            def _on_hover(drop_zone: DropZone | None):
                console.log(f'pointed dropzone: {drop_zone}')
                msg = (f'Insert new {element_def.tag_name}')
                if drop_zone:
                    pos = 'before' if drop_zone.position == Position.beforebegin else 'after'
                    # msg += f' at {drop_zone.position.name} of {drop_zone.element.tagName}'
                    msg += f' {pos} {drop_zone.element.tagName}'
                else:
                    msg += ' ... select a dropzone on the page.'
                self.property_editor.message1div.innerHTML = msg

            async def _start_drop_for_comp(event):
                _on_hover(None)
                res = await _drop_zone_start_selection_async(_on_hover, whole=False)
                logger.debug(f'_start_drop_for_comp res={res}')
                if res:
                    self.property_editor.set_state_selection_active()
                    await self._process_dropzone(res, element_def)
                else:
                    await self._canceled()

            element_html = f'<span style="cursor: pointer">{element_def.tag_name}</span> {_help_button(element_def)}'
            add_p(MenuMeta(element_def.tag_name, element_html), _start_drop_for_comp)

        for member in attrs:
            if member.meta.label == self.components_marker:
                [add_comp(ele_def) for ele_def in element_library.element_library().elements]
            else:
                help = member.meta.help
                if help:
                    help_html = '' if not help.url else info_link(help.url)
                    element_html = f'{help.description} {help_html}'
                    add_p(MenuMeta(help.description, element_html), partial(member, self))
                else:
                    add_p(member.meta, partial(member, self))
        self._update_toolbox_elements()

    async def _process_dropzone(self, drop_zone: DropZone, element_def: ElementDef):
        el_path = locator_from(drop_zone.element)

        if not el_path:
            window.alert(f'No component found for dropzone!')
            return

        logger.debug(f'element_path={el_path}')
        file = modlib._find_module_path(el_path.class_module)
        old_source = file.read_text()

        path_index = path_to_index(el_path.path)
        add_result = add_element(old_source, el_path.class_name, element_def, path_index, drop_zone.position)

        if isinstance(add_result, AddResult):
            logger.debug(f'write_module_file len={len(add_result.source_code)} el_path={el_path}')
            new_element_path = Locator(el_path.class_module, el_path.class_name, add_result.node_path,
                                       el_path.origin)
            self._toolbox_state.selected_element_path = new_element_path
            write_res = await rpc.write_module_file(el_path.class_module, add_result.source_code)
            logger.debug(f'write_module_file res={write_res}')
        elif isinstance(add_result, AddFailed):
            js.alert('Sorry, an error occurred while adding the component.')
            _open_error_reporter_window(
                'Error report data:\n\n' + add_result.exception_report_b64,
                title='Error report add_component - wwwpy'
            )
            # pre1: js.HTMLElement = js.document.createElement('pre')
            # pre1.innerText = self.path.read_text()
            # win.element.append(pre1)

    def _manage_toolbox_state(self):
        self._toolbox_state = state._restore(ToolboxState)
        self.inputSearch.value = self._toolbox_state.toolbox_search
        self._window.set_geometry(Geometry(*self._toolbox_state.geometry))

        def on_toolbar_geometry_change():
            g = self._window.geometry()
            acceptable_geometry = g.width > 100 and g.height > 100 and g.top > 0 and g.left > 0
            if acceptable_geometry:
                self._toolbox_state.geometry = self._window.geometry()

        self._window.geometry_change_listeners.append(on_toolbar_geometry_change)
        self._restore_selected_element_path()

    def inputSearch__input(self, e: Event):
        self._toolbox_state.toolbox_search = self.inputSearch.value
        self._update_toolbox_elements()

    def _update_toolbox_elements(self):
        def search_match(meta: MenuMeta):
            search = self.inputSearch.value.lower()
            lbl = meta.label.lower()
            starts_with = search.startswith(' ') and lbl.startswith(search.lstrip())
            ends_with = search.endswith(' ') and lbl.endswith(search.rstrip())
            if starts_with or ends_with:
                return True
            return search in lbl

        self.body.innerHTML = ''
        for meta in self._all_items:
            p = meta.p_element
            if meta.always_visible or search_match(meta):
                self.body.appendChild(p)

    async def _select_clear_btn__click(self, e: Event):
        self._toolbox_state.selected_element_path = None
        self._restore_selected_element_path()

    async def _select_element_btn__click(self, e: Event):
        no_comp = 'Select an element on the page to be inspected and edited...'
        self.property_editor.message1div.innerHTML = no_comp

        def _on_hover(drop_zone: DropZone | None):
            msg = no_comp
            if drop_zone:
                msg = 'Click to select ' + _element_lbl(drop_zone.element)
            self.property_editor.message1div.innerHTML = msg
            console.log(f'pointed dropzone: {drop_zone}')

        res = await _drop_zone_start_selection_async(_on_hover, whole=True)
        if res:
            self.property_editor.set_state_selection_active()
            self._toolbox_state.selected_element_path = locator_from(res.element)
        else:
            await self._canceled()
        self._restore_selected_element_path()

    # @menu(Help("Open errore reporter", ''))
    # async def _open_error_reporter(self, e: Event):
    #     _open_error_reporter_window('test error report body')

    @menu(Help('Create new component', _help_url('add_component')))
    async def _add_new_component(self, e: Event):
        if js.window.confirm('Add new component file?\nIt will be added to your "remote" folder.'):
            res = await rpc.add_new_component()
            js.window.alert(res)

    @menu(Help("Explore local filesystem", _help_url('remote_filesystem')))
    async def _browse_local_filesystem(self, e: Event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        filesystem_tree.show_explorer(DevModeComponent.instance.root_element())

    @menu(Help("Python console", ''))
    async def _python_console(self, e: Event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        w1 = new_window('Python console')
        from wwwpy.remote.designer.ui.python_console import PythonConsoleComponent
        w1.element.append(PythonConsoleComponent().element)
        DevModeComponent.instance.root_element().append(w1.element)

    @menu(Help("Logger levels", ''))
    async def _python_console(self, e: Event):
        from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
        w1 = new_window('Logger levels')

        w1.element.append(LoggerLevelsComponent().element)
        DevModeComponent.instance.root_element().append(w1.element)

    @menu(components_marker)
    def _drop_zone_start(self, e: Event):
        assert False, 'Just a placeholder'

    # @menu('handle global click')
    def _handle_global_click(self, e: Event):
        # add input
        def global_click(event: Event):
            event.preventDefault()
            event.stopImmediatePropagation()
            event.stopPropagation()
            console.log('global click', event.element)
            if self._global_click:
                document.removeEventListener('click', self._global_click, True)
                self._global_click = None

        self._global_click = create_proxy(global_click)
        document.addEventListener('click', self._global_click, True)

    def _restore_selected_element_path(self):
        element_path = self._toolbox_state.selected_element_path
        if element_path:
            logger.debug(f'restoring selected element path: {element_path}')
            if not element_path.valid():
                element_path = None
                logger.warning(f'invalid element path, setting to None')

        if element_path:
            self._select_clear_btn.style.visibility = 'visible'
        else:
            self._select_clear_btn.style.visibility = 'hidden'

        self.property_editor.selected_element_path = element_path

    async def _canceled(self):
        self.property_editor.message1div.innerHTML = 'Operation canceled'
        await asyncio.sleep(2)
        self.property_editor.message1div.innerHTML = ''


def is_inside_toolbar(element: HTMLElement | None):
    if not element:
        return False

    orig = element
    # loop until the root element and see if it is the toolbar
    res = False
    while element:
        if element.tagName.lower() == ToolboxComponent.component_metadata.tag_name:
            res = True
            break
        element = element.parentElement

    return res


def _default_drop_zone_accept(drop_zone: DropZone):
    element = drop_zone.element
    name = element.tagName.lower()
    from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
    root_elements = name == 'body' or name == 'html'
    wwwpy_elements = name == DevModeComponent.component_metadata.tag_name or is_inside_toolbar(element)
    accept = not (root_elements or wwwpy_elements)
    return accept


async def _drop_zone_start_selection_async(on_hover: DropZoneHover, whole: bool) -> Optional[DropZone]:
    from wwwpy.remote.designer.drop_zone import drop_zone_selector

    event = asyncio.Event()
    result = []

    def intercept_ended(ev: InterceptorEvent):
        console.log('intercept_ended', ev.target)
        ev.preventAndStop()
        selected = drop_zone_selector.stop()
        ev.uninstall()
        if selected:
            selected: DropZone
            console.log(
                f'\nselection accepted position {selected.position.name}'
                f'\ntarget: ', selected.element,
                '\nparent: ', selected.element.parentElement,
                '\nevent: ', ev.event,
                '\ncomposedPath: ', ev.event.composedPath(),
            )
            result.append(selected)
        else:
            console.log('intercept_ended - canceled')
        event.set()

    GlobalInterceptor(intercept_ended, 'pointerdown').install()

    click_inter = GlobalInterceptor(lambda ev: ev.preventAndStop(), 'click')
    click_inter.install()
    drop_zone_selector.start_selector(on_hover, _default_drop_zone_accept, whole=whole)
    await event.wait()
    console.log('drop_zone_selector event ended')

    async def _click_inter_uninstall():
        await asyncio.sleep(0.5)
        click_inter.uninstall()

    asyncio.ensure_future(_click_inter_uninstall())

    if len(result) == 0:
        return None

    return result[0]


def _open_error_reporter_window(body: str, title='Error reporter - wwwpy'):
    win = new_window(title, closable=True)
    mailto_component = MailtoComponent()
    mailto_component.subject = title
    mailto_component.recipient = 'simone.giacomelli@gmail.com'
    mailto_component.body = body
    mailto_component.text_content = 'Click here to send an email with the error report'
    mailto_component.element.style.display = 'block'
    mailto_component.element.style.textAlign = 'center'
    div: js.HTMLElement = js.document.createElement('div')

    action = '<h3>Please, help us improve wwwpy by sending this error report</h3>'
    div.insertAdjacentHTML('beforeend', action)
    div.append(mailto_component.element)
    div.style.margin = '15px'
    win.element.append(div)
    div.insertAdjacentHTML('beforeend', '<br>')
    js.document.body.append(win.element)

    from wwwpy.remote.designer.ui.dev_mode_component import DevModeComponent
    DevModeComponent.instance.root_element().append(win.element)
