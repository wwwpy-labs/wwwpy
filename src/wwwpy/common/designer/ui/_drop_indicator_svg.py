import logging

from wwwpy.common.designer.html_edit import Position

logger = logging.getLogger(__name__)


def position_for(width: float, height: float, x: float, y: float) -> Position:
    ratio = 0.35
    iw = width * ratio
    ih = height * ratio
    x0 = (width - iw) / 2
    y0 = (height - ih) / 2
    inside_inner = x0 <= x <= x0 + iw and y0 <= y <= y0 + ih
    if inside_inner:
        ix = x - x0
        iy = y - y0
        tl = _is_top_left(iw, ih, ix, iy)
        res = Position.afterbegin if tl else Position.beforeend
    else:
        tl = _is_top_left(width, height, x, y)
        res = Position.beforebegin if tl else Position.afterend
    logger.debug(f'position_for: x={x}, y={y}, iw={iw}, ih={ih}, x0={x0}, y0={y0}, res={res}')
    return res


def _is_top_left(w: float, h: float, x: float, y: float) -> bool:
    return y <= -h / w * x + h


def svg_indicator_for(width: float, height: float, position: Position) -> str:
    inactive_color = 'gray'
    active_color = 'green'
    iw = width * 25 / 70
    ih = height * 10 / 30
    x = (width - iw) / 2
    y = (height - ih) / 2
    out_tl = position == Position.beforebegin  # outer top left
    out_br = position == Position.afterend  # outer bottom right
    inn_tl = position == Position.afterbegin  # inner top left
    inn_br = position == Position.beforeend  # inner bottom right

    out_tl_color = active_color if out_tl else inactive_color
    out_br_color = active_color if out_br else inactive_color
    out_tl_width = 6 if out_tl else 2
    out_br_width = 6 if out_br else 2

    inn_tl_color = active_color if inn_tl else inactive_color
    inn_br_color = active_color if inn_br else inactive_color
    inn_tl_width = 3 if inn_tl else 1
    inn_br_width = 3 if inn_br else 1

    # language=html
    svg = '''<svg width="%(w)s" height="%(h)s" viewBox="0 0 %(w)s %(h)s" xmlns="http://www.w3.org/2000/svg">
  <g stroke="%(out_tl_color)s" stroke-width="%(out_tl_width)s">
    <line x1="0" y1="0" x2="%(w)s" y2="0"/>
    <line x1="0" y1="0" x2="0" y2="%(h)s"/>
  </g>
  <g stroke="%(out_br_color)s" stroke-width="%(out_br_width)s">
    <line x1="0" y1="%(h)s" x2="%(w)s" y2="%(h)s"/>
    <line x1="%(w)s" y1="0" x2="%(w)s" y2="%(h)s"/>
  </g>
  
  <g stroke="%(inn_tl_color)s" stroke-width="%(inn_tl_width)s" transform="translate(%(x)s, %(y)s)">
    <line x1="0" y1="0" x2="%(iw)s" y2="0"/>
    <line x1="0" y1="0" x2="0" y2="%(ih)s"/>
  </g>
  <g stroke="%(inn_br_color)s" stroke-width="%(inn_br_width)s" transform="translate(%(x)s, %(y)s)">
    <line x1="0" y1="%(ih)s" x2="%(iw)s" y2="%(ih)s"/>
    <line x1="%(iw)s" y1="0" x2="%(iw)s" y2="%(ih)s"/>
  </g>
  
</svg>'''
    return svg % dict(
        w=width, h=height,
        iw=iw, ih=ih,
        x=x, y=y,
        out_tl_color=out_tl_color, out_br_color=out_br_color,
        out_tl_width=out_tl_width, out_br_width=out_br_width,

        inn_tl_width=inn_tl_width, inn_tl_color=inn_tl_color,
        inn_br_width=inn_br_width, inn_br_color=inn_br_color,
    )


# language=html
_animate = """<animate attributeName="stroke" values="black;white;black" dur="1.5s" repeatCount="indefinite"/>"""

# language=html
_animate_transform = """
<animateTransform attributeName="transform" type="translate" values="3,3; 10,10; 3,3"
                dur="1s" repeatCount="indefinite" additive="sum"/>
                """
# language=html
_svg_at_begin = f"""
<svg [attrs] viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Main diagonal line (arrow body) - shorter -->
        <line x1="70" y1="70" x2="0" y2="0" stroke-width="6" stroke="black">{_animate}</line>
        <!-- First arrowhead segment -->
        <line x1="-3" y1="0" x2="47" y2="0" stroke-width="6" stroke="black">{_animate}</line>
        <!-- Second arrowhead segment -->
        <line x1="0" y1="-3" x2="0" y2="47" stroke-width="6" stroke="black">{_animate}</line>
        
        {_animate_transform}
    </g>
</svg>
"""
# language=html
_svg_at_end = f"""

<svg  [attrs] viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <g>
        <!-- Main diagonal line (arrow body) - shorter -->
        <line x1="30" y1="30" x2="100" y2="100" stroke-width="6" stroke="black">{_animate}</line>
        <!-- First arrowhead segment (horizontal) -->
        <line x1="53" y1="100" x2="103" y2="100" stroke-width="6" stroke="black">{_animate}</line>
        <!-- Second arrowhead segment (vertical) -->
        <line x1="100" y1="53" x2="100" y2="103" stroke-width="6" stroke="black">{_animate}</line>
        <animateTransform
                attributeName="transform"
                type="translate"
                values="-3,-3; -10,-10; -3,-3"
                dur="1s"
                repeatCount="indefinite"
                additive="sum"/>
    </g>
</svg>
"""

# language=html
_svg_at_inside = f"""
<svg [attrs] viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
todo
</svg>
"""
