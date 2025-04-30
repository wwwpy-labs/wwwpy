from typing import List

from wwwpy.common.designer.element_library import AttributeDef, Help, EventDef, ElementDef

ad_style = AttributeDef('style', Help('Inline style.',
                                      'https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/style'))
ad_class = AttributeDef('class', Help('A space-separated list of the classes of the element.',
                                      'https://developer.mozilla.org/en-US/docs/Web/API/Element/classList'))

ad_value = AttributeDef('value', Help('The value of the element.', ''))
ad_disabled = AttributeDef('disabled', Help('Whether the control is disabled.', ''), boolean=True)
ad_readonly = AttributeDef('readonly', Help('Whether the control is read-only.', ''), boolean=True)
ad_autofocus = AttributeDef('autofocus',
                            Help('Whether the control should have input focus when the page loads.', ''),
                            boolean=True)
ad_required = AttributeDef('required', Help('Whether the control is required for form submission.', ''),
                           boolean=True)
ad_placeholder = AttributeDef('placeholder', Help('A hint to the user of what can be entered in the field.', ''))
ad_name = AttributeDef('name', Help('Name of the control, useful for form submission.', ''))
ed_click = EventDef('click', Help('The element was clicked.',
                                  'https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event'))
ed_dblclick = EventDef('dblclick', Help('The element was double-clicked.',
                                        'https://developer.mozilla.org/en-US/docs/Web/API/Element/dblclick_event'))
ed_input = EventDef('input', Help('The input event fires when the value of the element has been changed '
                                  'as a direct result of a user action',
                                  'https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event'))
ed_keydown = EventDef('keydown', Help('The keydown event is fired when a key is pressed.'
                                      , 'https://developer.mozilla.org/en-US/docs/Web/API/Element/keydown_event'))
ed_keyup = EventDef('keyup', Help('The keyup event is fired when a key is released.',
                                  'https://developer.mozilla.org/en-US/docs/Web/API/Element/keyup_event'))
ed_change = EventDef('change', Help(
    'The change event is fired when a change to the element\'s value is committed by the user.',
    'https://developer.mozilla.org/en-US/docs/Web/API/Element/change_event'))

ed_pointerdown = EventDef('pointerdown', Help('The pointerdown event is fired when a pointer becomes active.',
                                              'https://developer.mozilla.org/en-US/docs/Web/API/Element/pointerdown_event'))

ed_pointerup = EventDef('pointerup', Help('The pointerup event is fired when a pointer is no longer active.',
                                          'https://developer.mozilla.org/en-US/docs/Web/API/Element/pointerup_event'))
ed_pointermove = EventDef('pointermove', Help('The pointermove event is fired when a pointer changes coordinates.',
                                              'https://developer.mozilla.org/en-US/docs/Web/API/Element/pointermove_event'))


def _insert_common_to_all(elements: List[ElementDef]):
    attrs = list(reversed([ad_style, ad_class]))
    events = [ed_click, ed_pointermove, ed_pointerup, ed_pointerdown, ed_keyup, ed_keydown]

    for element in elements:
        ea = element.attributes
        for attr in attrs:
            if ea.get(attr.name) is None:
                ea.insert(0, attr)

        ee = element.events
        for event in events:
            if ee.get(event.name) is None:
                ee.append(event)


def _create_unknown_element_def(tag_name: str) -> ElementDef:
    ed = ElementDef(tag_name, "", help=Help("", ""))
    _insert_common_to_all([ed])
    return ed
