from wwwpy.common.designer.html_edit import Position


def position_for(width: float, height: float, x: float, y: float) -> Position:
    # iw = width * 25 / 70
    # ih = height * 10 / 30
    ratio = 0.35
    iw = width * ratio
    ih = height * ratio
    x0 = (width - iw) / 2
    y0 = (height - ih) / 2
    if x0 <= x <= x0 + iw and y0 <= y <= y0 + ih:
        return Position.inside
    if y <= -height / width * x + height:
        return Position.beforebegin
    return Position.afterend


def svg_indicator_for(width: float, height: float, position: Position) -> str:
    inactive_color = 'gray'
    active_color = 'green'
    iw = width * 25 / 70
    ih = height * 10 / 30
    x = (width - iw) / 2
    y = (height - ih) / 2
    tl_color = active_color if position == Position.beforebegin else inactive_color
    br_color = active_color if position == Position.afterend else inactive_color
    rect_color = active_color if position == Position.inside else inactive_color
    # language=html
    svg = '''<svg width="%(w)s" height="%(h)s" viewBox="0 0 %(w)s %(h)s" xmlns="http://www.w3.org/2000/svg">
  <g stroke="%(tl_color)s" stroke-width="5">
    <line x1="0" y1="0" x2="%(w)s" y2="0"/>
    <line x1="0" y1="0" x2="0" y2="%(h)s"/>
  </g>
  <g stroke="%(br_color)s" stroke-width="5">
    <line x1="0" y1="%(h)s" x2="%(w)s" y2="%(h)s"/>
    <line x1="%(w)s" y1="0" x2="%(w)s" y2="%(h)s"/>
  </g>
  <rect x="%(x)s" y="%(y)s" width="%(iw)s" height="%(ih)s" fill="none" stroke="%(rect_color)s" 
    stroke-width="2.5"/>
</svg>'''
    return svg % dict(
        w=width, h=height,
        iw=iw, ih=ih,
        x=x, y=y,
        tl_color=tl_color,
        br_color=br_color,
        rect_color=rect_color
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
