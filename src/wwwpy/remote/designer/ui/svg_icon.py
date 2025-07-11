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
    host_style: dict[str, str]

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
<style data-name="_style">
:host { display: flex; border: 0px solid transparent ; --svg-primary-color: #2B2D30;  }
:host(:hover) { --svg-primary-color: #3C3E41; }
svg { display: block }
</style>
<div data-name="_div"></div>
        """
        self.active = False
        self.host_style: dict[str, str] = dict()
        self.host_style['border'] = '5px solid transparent'

    def _set_style(self, source='na'):
        color, hover_color = (_BLUE, '') if self.active else (_BGRD, _GRAY)

        logger.warning(f'_set_style: {source}')
        sheet = self._style.sheet

        js.console.log('=' * 10, self._style, sheet)
        if not sheet or not sheet.cssRules:
            logger.warning('No CSS rules found in the style element.')
            return

        cssRules = list(self._style.sheet.cssRules)
        host_normal = cssRules[0]
        host_normal.style.setProperty('--svg-primary-color', color)
        for key, value in self.host_style.items():
            host_normal.style.setProperty(key, value)

        host_hover = cssRules[1]
        host_hover.style.setProperty('--svg-primary-color', hover_color)
        return
        # language=html
        hover_style = ":host(:hover) { --svg-primary-color: %s; }" % (hover_color,) if hover_color else ''
        s = ('svg { display: block }\n' +
             ':host { display: flex; border: %spx solid transparent }\n' % self.border +
             ':host { --svg-primary-color: %s; }\n' % color + hover_style)
        logger.debug(f'set_style: `{s}`')
        self._style.innerHTML = s

    def load_svg_str(self, svg: str):
        self._div.innerHTML = add_rounded_background2(svg, 'var(--svg-primary-color)')
        self._set_style()

    @property
    def active(self) -> bool:
        # todo probably rename to 'selected' and add new property 'disabled'
        #  if disabled, change the colors accordingly; if not disabled honor the colors from the active property
        return self._active

    @active.setter
    def active(self, value: bool):
        self._active = value
        self._set_style('active')

    def connectedCallback(self):
        self._set_style('connectedCallback')

    def _div__click(self, event):
        self.active = not self.active
