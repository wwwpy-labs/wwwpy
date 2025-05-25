from __future__ import annotations

import logging
from pathlib import Path

import js

import wwwpy.remote.component as wpc
from wwwpy.common.designer.ui.svg import add_rounded_background2
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)

_BLUE = '#3574F0'
_GRAY = '#3C3E41'
_BGRD = '#2B2D30'


class SvgIcon(wpc.Component, tag_name='wwwpy-svg-icon'):
    filename: str = wpc.attribute()
    _style: js.HTMLStyleElement = wpc.element()
    _div: js.HTMLDivElement = wpc.element()
    _active: bool
    border: int = 5

    @classmethod
    def from_file(cls, file: Path) -> SvgIcon:
        r = cls()
        r.load_svg_str(file.read_text())
        r.element.setAttribute('title', file.name)
        return r

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style data-name="_style"></style>
<div data-name="_div"></div>
        """

        self.active = False

    def load_svg_str(self, svg: str):
        self._div.innerHTML = add_rounded_background2(svg, 'var(--svg-primary-color)')

    @property
    def active(self) -> bool:
        # todo probably rename to 'selected' and add new property 'disabled'
        #  if disabled, change the colors accordingly; if not disabled honor the colors from the active property
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        root, hover = (_BLUE, '') if value else (_BGRD, _GRAY)
        self._set_style(root, hover)

    def _set_style(self, color: str, hover_color: str):
        # language=html
        hover_style = ":host(:hover) { --svg-primary-color: %s; }" % (hover_color,) if hover_color else ''
        s = ('svg { display: block }\n' +
             ':host { border: %spx solid transparent }\n' % self.border +
             ':host { --svg-primary-color: %s; }\n' % color + hover_style)
        logger.debug(f'set_style: `{s}`')
        self._style.innerHTML = s

    def _div__click(self, event):
        self.active = not self.active
