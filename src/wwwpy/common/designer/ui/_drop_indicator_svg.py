from wwwpy.common.designer.html_edit import Position


# def position_for(width: int, height: int, x: int, y: int) -> Position:
#     pass
def svg_indicator_for(width: float, height: float, position: Position) -> str:

    if position == Position.beforebegin:
        txt = _svg_at_begin
        ar = 'xMinYMid' if width > height else 'xMidYMin'
    elif position == Position.afterend:
        txt = _svg_at_end
        ar = 'xMaxYMid' if width > height else 'xMidYMax'
    elif position == Position.inside:
        txt = _svg_at_inside
        ar = 'xMidYMid'
    else:
        raise ValueError(f"Unknown position: {position}")

    # txt = txt.replace('width: 200px', f'width: {int(width)}px')
    # txt = txt.replace('height: 200px', f'height: {int(height)}px')

    attrs = f'style="width: {int(width)} height:{int(height)}" '
    attrs += f' preserveAspectRatio="{ar} meet"'
    txt = txt.replace('[attrs]', attrs)
    return txt


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
