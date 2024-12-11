from pathlib import Path
from typing import List

from wwwpy.common.collectionlib import ListMap
from wwwpy.common.designer.el_common import ed_click, ed_keydown, ed_input, ad_style, _insert_common_to_all
from wwwpy.common.designer.element_library import ElementDef, EventDef, Help, NamedListMap, AttributeDef
from wwwpy.common.rpc import serialization

parent = Path(__file__).parent


#
def _reorder(elements: List[ElementDef]):
    hide = {'sl-drawer', 'sl-radio', 'sl-dialog', 'sl-include', 'sl-menu-label',
            'sl-radio-button', 'sl-animation', 'sl-breadcrumb', 'sl-popup',
            'sl-breadcrumb-item', 'sl-carousel-item', 'sl-menu-item', 'sl-tree-item'}
    for e in elements.copy():
        if e.tag_name in hide:
            elements.remove(e)

    order = ['sl-button', 'sl-input', 'sl-textarea',
             'sl-checkbox', 'sl-switch', 'sl-progress-bar', 'sl-split-panel',
             'sl-textarea', 'sl-alert', 'sl-select', 'sl-dropdown']

    order.reverse()
    by_tag_name = {element.tag_name: element for element in elements}

    for o in order:
        ed = by_tag_name.get(o)
        if not ed:
            raise ValueError(f"Element {o} not found")
        elements.remove(ed)
        elements.insert(0, ed)


def _set_icon_values(elements: List[ElementDef], tag_names: List[str]):
    icon_values = (parent / 'sl_icons.txt').read_text().split('\n')
    for tag_name in tag_names:
        element = elements.get(tag_name)
        if not element:
            continue
        attribute = element.attributes.get('name')
        if not attribute:
            continue
        attribute.values = icon_values


def _insert_event(elements: List[ElementDef], tag_names, event_def: EventDef):
    for tag_name in tag_names:
        element = elements.get(tag_name)
        if not element:
            continue
        element.events.insert(0, event_def)


def _insert_attribute(elements: List[ElementDef], tag_names, attribute_name: str):
    for tag_name in tag_names:
        element: ElementDef = elements.get(tag_name)
        if not element:
            continue
        attr = AttributeDef(attribute_name)
        element.attributes.insert(0, attr)


def _shoelace_elements_def() -> List[ElementDef]:
    shoelace_json = (parent / 'el_shoelace.json').read_text()
    elements = serialization.from_json(shoelace_json, List[ElementDef])
    elements = ListMap(elements, key_func=lambda x: x.tag_name)
    for element in elements:
        element.gen_html = _shoelaceGenerateHtml

    _set_icon_values(elements, ['sl-icon', 'sl-icon-button'])
    _insert_event(elements, ['sl-button', 'sl-icon-button', 'sl-input',
                             'sl-textarea', 'sl-checkbox', ], ed_keydown)
    _insert_event(elements, ['sl-button', 'sl-icon-button', 'sl-input',
                             'sl-textarea', 'sl-checkbox', 'sl-progress-bar'], ed_click)
    _insert_event(elements, ['sl-input', 'sl-textarea', 'sl-checkbox'], ed_input)

    _insert_common_to_all(elements)

    _reorder(elements)
    return elements


def _shoelaceGenerateHtml(element_def: ElementDef, name: str) -> str:
    tag_name = element_def.tag_name

    def _def(placeHolder=False, add='', content=None):
        def inner():
            pl = '' if not placeHolder else f' placeholder="{name}"'
            add1 = '' if not add else f' {add}'
            ic = name if content is None else content
            return f'<{tag_name} data-name="{name}"{pl}{add1}>{ic}</{tag_name}>'

        return inner

    func = {
        'sl-button': _def(),
        'sl-input': lambda: f"""<sl-input data-name="{name}" placeholder="{name}"></sl-input>""",
        'sl-textarea': _def(placeHolder=True, content=''),
        'sl-select': lambda: f'''<sl-select data-name="{name}" label="Select a Few" value="option-2" multiple clearable max-options-visible="0">
    <sl-option value="option-1">Option 1</sl-option>
    <sl-option value="option-2">Option 2</sl-option>
    <sl-option value="option-3">Option 3</sl-option>
</sl-select>''',
        'sl-checkbox': _def(),
        'sl-radio-group': lambda: f"""<sl-radio-group data-name="{name}" label="Select an option" name="a" value="1">
    <sl-radio value="1">Option 1</sl-radio>
    <sl-radio value="2">Option 2</sl-radio>
    <sl-radio value="3">Option 3</sl-radio>
</sl-radio-group>""",
        'sl-switch': _def(),
        'sl-alert': lambda: f"""<sl-alert data-name="{name}" variant="primary" open closable>
    <sl-icon slot="icon" name="info-circle"></sl-icon>
    You can close this alert any time!
</sl-alert>""",
        'sl-badge': _def(),
        'sl-card': lambda: f'''<sl-card data-name="{name}" class="card-overview">
    <img slot="image" src="https://images.unsplash.com/photo-1559209172-0ff8f6d49ff7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=500&q=80" alt="A kitten sits patiently between a terracotta pot and decorative grasses."/>
    <strong>Mittens</strong><br />
    This kitten is as cute as he is playful. Bring him home today!<br />
    <small>6 weeks old</small>
    <div slot="footer">
        <sl-button variant="primary" pill>More Info</sl-button>
        <sl-rating></sl-rating>
    </div>
</sl-card>''',
        'sl-dialog': lambda: f'''<sl-dialog data-name="{name}" label="{name}" open><sl-button slot="footer" variant="primary">Close</sl-button></sl-dialog>''',
        'sl-drawer': lambda: f'''<sl-drawer data-name="{name}" open label="Drawer" placement="end" class="drawer-placement-start">
    <span>Drop elements here.<br>To close the drawer with Python set {name}.open=False<br>In html, remove the attribute `open`</span>
</sl-drawer>''',
        'sl-dropdown': lambda: f'''<sl-dropdown data-name="{name}">
    <sl-button slot="trigger" caret>{name}</sl-button>
    <sl-menu>
        <sl-menu-item>Item 1</sl-menu-item>
        <sl-menu-item>Item 2</sl-menu-item>
        <sl-menu-item>Item 3</sl-menu-item>
    </sl-menu>
</sl-dropdown>''',
        'sl-tooltip': lambda: f'''<sl-tooltip data-name="{name}" content="{name}"><sl-button>Hover Me</sl-button></sl-tooltip>''',
        'sl-progress-bar': _def(add='value="50"'),
        'sl-image-comparer': lambda: f'''<sl-image-comparer data-name="{name}">
    <img slot="before" src="https://images.unsplash.com/photo-1517331156700-3c241d2b4d83?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=800&q=80&sat=-100&bri=-5" alt="Grayscale version of kittens in a basket looking around." />
    <img slot="after" src="https://images.unsplash.com/photo-1517331156700-3c241d2b4d83?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=800&q=80" alt="Color version of kittens in a basket looking around." />
</sl-image-comparer>''',
        'sl-avatar': lambda: f"""<sl-avatar data-name="{name}" 
    image="https://images.unsplash.com/photo-1591871937573-74dbba515c4c?ixlib=rb-1.2.1&auto=format&fit=crop&w=300&q=80"
    label="Avatar of a white and grey kitten on grey textile"></sl-avatar>""",
        'sl-skeleton': lambda: """<div style="display: block; width: 70%">
  <header style="display: flex; align-items: center; margin-bottom: 1rem;">
    <sl-skeleton style="float: left; width: 3rem; height: 3rem; margin-right: 1rem; vertical-align: middle;"></sl-skeleton>
    <sl-skeleton style="flex: 0 0 auto; width: 30%;"></sl-skeleton>
  </header>

  <sl-skeleton style="width: 95%; margin-bottom: 1rem;"></sl-skeleton>
  <sl-skeleton style="width: 80%; margin-bottom: 1rem;"></sl-skeleton>
  <sl-skeleton style="width: 60%;  margin-bottom: 1rem;"></sl-skeleton>
</div>""",
        'sl-spinner': _def(),
        'sl-icon': _def(add='name="star"'),
        'sl-icon-button': lambda: f'''<sl-icon-button data-name="{name}" name="house-gear"></sl-icon-button>''',
        'sl-split-panel': lambda: f'''<sl-split-panel data-name="{name}" position="25" style="height: 300px; --divider-width: 20px; background: var(--sl-color-neutral-50);">
    <sl-icon slot="divider" name="grip-vertical"></sl-icon>
    <div slot="start" style="display: flex; align-items: center; justify-content: center; overflow: hidden;">
        <span>Start</span>
    </div>
    <div slot="end" style="display: flex; align-items: center; justify-content: center; overflow: hidden;">
        <span>End<br>You can change orientation setting the attribute `vertical`</span>
    </div>
</sl-split-panel>''',
        'sl-tree': lambda: f"""<sl-tree data-name="{name}" selection="multiple">
    <sl-tree-item expanded><sl-icon name="folder"></sl-icon>
        Documents
        <sl-tree-item><sl-icon name="folder"></sl-icon>
            Photos
            <sl-tree-item><sl-icon name="image"></sl-icon>birds.jpg</sl-tree-item>
            <sl-tree-item><sl-icon name="image"></sl-icon>kitten.jpg</sl-tree-item>
            <sl-tree-item><sl-icon name="image"></sl-icon>puppy.jpg</sl-tree-item>
        </sl-tree-item>

        <sl-tree-item>
            <sl-icon name="folder"></sl-icon>Writing
            <sl-tree-item><sl-icon name="file"></sl-icon>draft.txt</sl-tree-item>
            <sl-tree-item><sl-icon name="file-pdf"></sl-icon>final.pdf</sl-tree-item>
            <sl-tree-item><sl-icon name="file-bar-graph"></sl-icon>sales.xls</sl-tree-item>
        </sl-tree-item>
    </sl-tree-item>
</sl-tree>""",
        'sl-progress-ring': lambda: f"""<sl-progress-ring data-name="{name}" value="35"></sl-progress-ring>""",
        'sl-carousel': lambda: f"""<sl-carousel data-name="{name}" autoplay pagination navigation loop mouse-dragging>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1464822759023-fed622ff2c3b" alt="Green mountain across body of water"></sl-carousel-item>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1501785888041-af3ef285b470" alt="three brown wooden boat on blue lake water taken at daytime"></sl-carousel-item>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1532274402911-5a369e4c4bb5" alt="brown wooden dock between lavender flower field near body of water during golden hour"></sl-carousel-item>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1523712999610-f77fbcfc3843" alt="forest heat by sunbeam"></sl-carousel-item>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1472214103451-9374bd1c798e" alt="green grass field during sunset"></sl-carousel-item>
    <sl-carousel-item><img src="https://images.unsplash.com/photo-1501785888041-af3ef285b470" alt="three brown wooden boat on blue lake water taken at daytime"></sl-carousel-item>
</sl-carousel>""",
        'sl-details': lambda: f"""<sl-details data-name="{name}" summary="Toggle Me">
  Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna
  aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
</sl-details>""",
        'sl-animated-image': lambda: f"""<sl-animated-image data-name={name} src="https://shoelace.style/assets/images/tie.webp" alt="Animation of a shoe being tied"></sl-animated-image>"""

    }
    gen_html = func.get(tag_name, None)
    html = '\n' + gen_html() if gen_html else '' + ElementDef.default_gen_html(element_def, name)
    return html
