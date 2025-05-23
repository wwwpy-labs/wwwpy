from __future__ import annotations

from js import HTMLElement, console

from wwwpy.common.designer.element_editor import ElementEditor, EventEditor
from wwwpy.common.designer.element_library import ElementDef
from wwwpy.common.designer.locator_lib import Locator
from wwwpy.remote.designer.locator_js import locator_from

try:
    from wwwpy.server.designer import rpc
except ImportError:
    from wwwpy.common._raise_on_any import RaiseOnAny

    rpc = RaiseOnAny('During testing this rpc is not (yet) configured')  # todo


async def _rpc_save(el_path: Locator, new_source: str):
    await rpc.write_module_file(el_path.class_module, new_source)


def info_link(href):
    # open in a new page
    # <a href='https://www.google.com' target='_blank'><svg class="help-icon"><use href="#help-icon"/></svg></a>
    # language=html
    return f"""<wwwpy-help-icon href="{href}"></wwwpy-help-icon>"""

    return (f'<a href="{href}" style="text-decoration: none" target="_blank">'
            f'<svg class="help-icon"><use href="#help-icon"/></svg></a>')


def _element_lbl(element: HTMLElement) -> str:
    ep = locator_from(element)
    console.log(f'element_path={ep}')
    return _element_path_lbl(ep) if ep else 'No element path'


def _element_path_lbl(ep: Locator | None) -> str:
    from wwwpy.common import modlib
    class_file_path = modlib._find_module_path(ep.class_module)
    cfp = '' if not class_file_path else f'{class_file_path.name}::'
    lbl = '' if not ep.data_name else f' ({ep.data_name})'
    msg = f'{ep.tag_name} element {lbl} in {cfp}{ep.class_name}'
    return msg


async def _log_event(element_editor: ElementEditor, event_editor: EventEditor):
    ep = element_editor.element_path
    ee = ElementEditor(ep, element_editor.element_def)
    ev = ee.events.get(event_editor.definition.name)
    message = f'\nClick below to locate the event handler {ev.method.name}'
    await rpc.print_module_line(ep.class_module, message, ev.method.code_lineno)


def _help_button(element_def: ElementDef) -> str:
    help_url = element_def.help.url
    help_button = '' if len(help_url) == 0 else info_link(element_def.help.url)
    return help_button


async def _on_error(message, source, lineno, colno, error):
    await rpc.on_error(message, source, lineno, colno, str(error))


async def _on_unhandledrejection(event):
    try:
        await rpc.on_unhandledrejection(f'{event.reason}')
    except Exception as ex:
        # trap and send to the console, otherwise we will trigger this handler again going into an infinite loop
        console.error(f'Error in on_unhandledrejection: {ex}')


def _help_url(help_str: str) -> str:
    return f'https://wwwpy.dev/help/{help_str}.html'
