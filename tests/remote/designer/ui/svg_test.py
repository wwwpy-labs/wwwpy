import logging

import js
import pytest

from wwwpy.common.designer.ui.rect_readonly import rect_to_py
from wwwpy.common.designer.ui.svg import add_rounded_background2

logger = logging.getLogger(__name__)
_BLUE = '#3574F0'
_GRAY = '#3C3E41'


@pytest.mark.parametrize("color", ['#2B2D30', _BLUE, _GRAY])
def test_svg_is_rendered(color):
    svg_str = add_rounded_background2(_svg1, color)
    logger.debug(f'svg_str: ```{svg_str}```')
    f = js.document.createRange().createContextualFragment(svg_str)
    assert f.childElementCount == 1
    assert f.firstChild.tagName == 'svg'
    svg = f.firstElementChild
    js.document.body.appendChild(f)
    rect = rect_to_py(svg.getBoundingClientRect())
    logger.debug(f'rect: {rect}')
    assert rect.width > 0
    assert rect.height > 0


def _append(svg2):
    f = js.document.createRange().createContextualFragment(svg2)
    js.document.body.appendChild(f)


# language=html
_svg1 = """
<!-- Copyright 2000-2022 JetBrains s.r.o. and contributors. Use of this source code is governed by the Apache 2.0 license. -->
<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M10.5199 5.57617L10.7285 5.75H11H17C17.6904 5.75 18.25 6.30964 18.25 7V15.1667C18.25 16.0671 17.553 16.75 16.75 16.75H3.25C2.44705 16.75 1.75 16.0671 1.75 15.1667V4.83333C1.75 3.93294 2.44705 3.25 3.25 3.25H7.63795C7.69643 3.25 7.75307 3.2705 7.798 3.30794L10.5199 5.57617Z" stroke="#CED0D6" stroke-width="1.5"/>
</svg>

"""
# language=html
_svg2 = """
<!-- Copyright © 2000–2024 JetBrains s.r.o. -->
<svg width="20" height="20" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
  <path fill="none" stroke="#CED0D6" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 18.15v-15c0-.69-.56-1.25-1.25-1.25H3.12c-.69 0-1.25.56-1.25 1.25V16.9c0 .69.56 1.25 1.25 1.25h13.75c.69 0 1.25-.56 1.25-1.25v-5.62c0-.69-.56-1.25-1.25-1.25H1.88"/>
  <path fill="none" stroke="#CED0D6" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M18.96 4.58c.19.19.29.45.29.7s-.1.51-.29.7l-3.51 3.51a.984.984 0 0 1-1.4 0l-3.51-3.51a.984.984 0 0 1 0-1.4l3.51-3.51c.97-.97 1.69.28 4.91 3.51"/>
</svg>
"""
