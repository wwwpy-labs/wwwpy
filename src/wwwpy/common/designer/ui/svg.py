import xml.etree.ElementTree as ET
from typing import Callable, Dict


def set_width_height(svg: str, width: float, height: float) -> str:
    root = ET.fromstring(svg)
    root.set('width', str(width))
    root.set('height', str(height))
    # return ET.tostring(root, encoding='unicode')
    out = ET.tostring(root, encoding='unicode')
    out = out.replace('ns0:', '').replace('xmlns:ns0=', 'xmlns=')
    return out


def add_rounded_background2(svg: str, fill_color: str, ratio: float = 1.4, radius: float = 5) -> str:
    r = add_rounded_background3(svg, fill_color, ratio, radius)
    r2 = set_width_height(r, 22, 22)
    return r2


def add_rounded_background3(svg: str, fill_color: str, ratio: float = 1.4, radius: float = 5) -> str:
    root = ET.fromstring(svg)
    orig_w = float(root.attrib['width'])
    orig_h = float(root.attrib['height'])
    assert orig_w == orig_h
    if 'viewBox' in root.attrib:
        x0, y0, vb_w, vb_h = map(float, root.attrib['viewBox'].split())
    else:
        x0 = y0 = 0.0
        vb_w = vb_h = orig_w
    assert vb_w == vb_h == orig_w
    new_size = orig_w * ratio
    offset = (orig_w - new_size) / 2

    def fmt(v):
        return str(int(v)) if v.is_integer() else str(v)

    new_s = fmt(new_size)
    off_s = fmt(offset)
    root.attrib['viewBox'] = f'{off_s} {off_s} {new_s} {new_s}'
    root.attrib['width'] = new_s
    root.attrib['height'] = new_s
    ns = '{http://www.w3.org/2000/svg}'
    bg = ET.Element(ns + 'rect', {
        'x': off_s,
        'y': off_s,
        'width': new_s,
        'height': new_s,
        'fill': fill_color,
        'rx': str(radius),
        'ry': str(radius)
    })
    root.insert(0, bg)
    for e in root.iter():
        if isinstance(e.tag, str) and e.tag.startswith(ns):
            e.tag = e.tag[len(ns):]
    for k in list(root.attrib):
        if k.startswith('xmlns'):
            root.attrib.pop(k)
    root.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
    return ET.tostring(root, encoding='unicode')


def add_rounded_background(svg: str, fill_color: str, radius: float) -> str:
    root = ET.fromstring(svg)
    x, y, w, h = root.attrib.get('viewBox', '0 0 0 0').split()
    ns = '{http://www.w3.org/2000/svg}'
    bg = ET.Element(ns + 'rect', {
        'x': x,
        'y': y,
        'width': w,
        'height': h,
        'fill': fill_color,
        'rx': str(radius),
        'ry': str(radius)
    })
    root.insert(0, bg)
    for e in root.iter():
        if isinstance(e.tag, str) and e.tag.startswith('{'):
            e.tag = e.tag.split('}', 1)[1]
    for k in list(root.attrib):
        if k.startswith('xmlns'):
            root.attrib.pop(k)
    root.attrib['xmlns'] = 'http://www.w3.org/2000/svg'
    return ET.tostring(root, encoding='unicode')


AttributeMutator = Callable[[Dict[str, str]], None]


def build_document(svg: str, attribute_mutator: AttributeMutator) -> str:
    root = ET.fromstring(svg)
    for elem in root.iter():
        attribute_mutator(elem.attrib)
    out = ET.tostring(root, encoding='unicode')
    out = out.replace('ns0:', '').replace('xmlns:ns0=', 'xmlns=')
    return out
