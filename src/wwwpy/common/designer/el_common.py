from wwwpy.common.designer.element_library import AttributeDef, Help, EventDef

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
ed_change = EventDef('change', Help(
    'The change event is fired when a change to the element\'s value is committed by the user.',
    'https://developer.mozilla.org/en-US/docs/Web/API/Element/change_event'))
