from typing import List

from wwwpy.common.designer.element_library import ElementDef, Help, EventDef, AttributeDef, NamedListMap


def _standard_elements_def() -> List[ElementDef]:
    res = [
        ElementDef(
            'button', 'js.HTMLButtonElement',
            help=Help('A clickable button.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button'),
            attributes=[
                AttributeDef('type', Help('The type of the button.', ''),
                             values=['submit', 'reset', 'button'], default_value='button'),
                AttributeDef('value', Help('The value of the button.', '')),
            ],
            events=[EventDef('click', Help('The button was clicked.',
                                           'https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event')),
                    EventDef('dblclick', Help('The button was double-clicked.',
                                              'https://developer.mozilla.org/en-US/docs/Web/API/Element/dblclick_event'))],
        ),
        ElementDef(
            'input', 'js.HTMLInputElement',
            help=Help('A field for entering text.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input'),
            attributes=[
                AttributeDef('type', Help('The type of control to display. The default type is text.', ''),
                             values=['text', 'password', 'checkbox', 'radio', 'button', 'submit', 'reset', 'file',
                                     'hidden', 'image', 'date', 'datetime-local', 'month', 'time', 'week',
                                     'number', 'range', 'email', 'url', 'search', 'tel', 'color'],
                             default_value='text'),
                AttributeDef('value', Help('The value of the input field.', '')),
                AttributeDef('placeholder', Help('A hint to the user of what can be entered in the field.', '')),
                AttributeDef('disabled', Help('Whether the control is disabled.', ''), boolean=True),
                AttributeDef('readonly', Help('Whether the control is read-only.', ''), boolean=True),
                AttributeDef('required', Help('Whether the control is required for form submission.', ''),
                             boolean=True),
                AttributeDef('min', Help('The minimum value of the input field.', '')),
                AttributeDef('max', Help('The maximum value of the input field.', '')),
                AttributeDef('step', Help('The legal number intervals for the input field.', '')),
                AttributeDef('pattern', Help('A regular expression that the input\'s value is checked against.', '')),
                AttributeDef('autocomplete', Help('Whether the control is required for form submission.', ''),
                             values=['on', 'off']),
                AttributeDef('autofocus', Help('Whether the control should have input focus when the page loads.', ''),
                             boolean=True),
                AttributeDef('checked', Help('Whether the control is checked.', ''), boolean=True),
                AttributeDef('multiple', Help('Whether the user is allowed to enter more than one value.', ''),
                             boolean=True),

            ],
            events=[
                EventDef('input', Help('The input event fires when the value of the element has been changed '
                                       'as a direct result of a user action',
                                       'https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event')),
                EventDef('change')
            ]
        ),
        ElementDef(
            'textarea', 'js.HTMLTextAreaElement',
            help=Help(
                'A multi-line text input control.',
                'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/textarea'
            ),
            attributes=[
                AttributeDef(
                    'cols',
                    Help('The visible width of the text control, in average character widths.', ''),
                    default_value='20'
                ),
                AttributeDef(
                    'rows',
                    Help('The number of visible text lines for the control.', ''),
                    default_value='2'
                ),
                AttributeDef(
                    'disabled',
                    Help('Whether the control is disabled.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'readonly',
                    Help('Whether the control is read-only.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'required',
                    Help('Whether the control is required for form submission.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'placeholder',
                    Help('A hint to the user of what can be entered in the field.', '')
                ),
                AttributeDef(
                    'autofocus',
                    Help('Whether the control should have input focus when the page loads.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'maxlength',
                    Help('The maximum number of characters that the user can enter.', '')
                ),
                AttributeDef(
                    'minlength',
                    Help('The minimum number of characters that the user can enter.', '')
                ),
                AttributeDef(
                    'wrap',
                    Help('How the control wraps text.', ''),
                    values=['soft', 'hard', 'off'],
                    default_value='soft'
                ),
                AttributeDef(
                    'autocomplete',
                    Help('Whether the control has autocomplete enabled.', ''),
                    values=['on', 'off'],
                    default_value='on'
                ),
                AttributeDef(
                    'spellcheck',
                    Help('Whether spell checking is enabled for the control.', ''),
                    values=['true', 'false'],
                    default_value='true'
                ),
                AttributeDef(
                    'form',
                    Help('The form element that the textarea is associated with (its id).', '')
                ),
                AttributeDef(
                    'name',
                    Help('Name of the control, useful for form submission.', '')
                ),
            ],
            events=[
                EventDef(
                    'input',
                    Help(
                        'The input event fires when the value of the element has been changed as a direct result of a user action.',
                        'https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event'
                    )
                ),
                EventDef(
                    'change',
                    Help(
                        'The change event is fired when a change to the element\'s value is committed by the user.',
                        'https://developer.mozilla.org/en-US/docs/Web/API/Element/change_event'
                    )
                ),
            ],
        ),
        ElementDef(
            'div', 'js.HTMLDivElement',
            help=Help('A generic container element.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div')
        ),
        ElementDef(
            'progress', 'js.HTMLProgressElement',
            help=Help('A progress bar.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/progress'),
            attributes=[
                AttributeDef('value', Help('The current value of the progress bar.', '')),
                AttributeDef('max', Help('The maximum value of the progress bar.', '')),
            ],
            events=[
                EventDef('click', Help('The progress bar was clicked.', '')),
            ]
        ),
        ElementDef(
            'select', 'js.HTMLSelectElement',
            help=Help(
                'A control that provides a menu of options.',
                'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/select'
            ),
            attributes=[
                AttributeDef(
                    'name',
                    Help('Name of the control, useful for form submission.', '')
                ),
                AttributeDef(
                    'disabled',
                    Help('Whether the control is disabled.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'multiple',
                    Help('Whether multiple options can be selected.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'required',
                    Help('Whether the control is required for form submission.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'size',
                    Help('Number of visible options.', ''),
                    default_value='1'
                ),
                AttributeDef(
                    'autofocus',
                    Help('Whether the control should have input focus when the page loads.', ''),
                    boolean=True
                ),
                AttributeDef(
                    'form',
                    Help('The form element that the select is associated with (its id).', '')
                ),
            ],
            events=[
                EventDef(
                    'change',
                    Help(
                        'The change event is fired when a change to the element\'s value is committed by the user.',
                        'https://developer.mozilla.org/en-US/docs/Web/API/Element/change_event'
                    )
                ),
                EventDef(
                    'input',
                    Help(
                        'The input event fires when the value of the element has been changed as a direct result of a user action.',
                        'https://developer.mozilla.org/en-US/docs/Web/API/Element/input_event'
                    )
                ),
            ],

        ),
        ElementDef(
            'meter', 'js.HTMLMeterElement',
            help=Help(
                'A scalar measurement within a known range (e.g., disk usage, battery level).',
                'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meter'
            ),
            attributes=NamedListMap([
                AttributeDef('value', Help('The current numeric value.', '')),
                AttributeDef('min', Help('The lower numeric bound of the measured range. Default is 0.', '')),
                AttributeDef('max', Help('The upper numeric bound of the measured range. Default is 1.', '')),
                AttributeDef('low', Help('The upper numeric bound of the low end of the measured range.', '')),
                AttributeDef('high', Help('The lower numeric bound of the high end of the measured range.', '')),
                AttributeDef('optimum', Help('The optimal numeric value.', '')),
                AttributeDef('form', Help('Associates the meter with a form element.', '')), ]
            ),
            events=NamedListMap([
                EventDef('click',
                         Help('The meter was clicked.',
                              'https://developer.mozilla.org/en-US/docs/Web/API/Element/click_event')
                         ),
            ]),
        )

    ]

    for r in res:
        r.gen_html = _generateHtml
    return res


def _generateHtml(element_def: ElementDef, name: str) -> str:
    tag_name = element_def.tag_name

    def _def(placeHolder=False, add='', inner=''):
        def inner_func():
            pl = '' if not placeHolder else f' placeholder="{name}"'
            add1 = '' if not add else f' {add}'
            content = name if not inner else inner
            return f'<{tag_name} data-name="{name}"{pl}{add1}>{content}</{tag_name}>'

        return inner_func

    func = {
        'button': _def(),
        'input': lambda: f'<input data-name="{name}" placeholder="{name}">',
        'progress': lambda: f'<progress data-name="{name}" value="70" max="100">70%</progress>',
        'textarea': _def(placeHolder=True),
        'select': _def(inner='''
            <option value="option1">Option 1</option>
            <option value="option2">Option 2</option>
            <option value="option3">Option 3</option>
        '''),
        'meter': _def(add='value="0.85" min="0" max="1" low="0.3" high="0.7" optimum="0.8"')
    }
    gen_html = func.get(tag_name, None)
    html = '\n' + gen_html() if gen_html else '' + ElementDef.default_gen_html(element_def, name)
    return html

# [
#     _comp('input', 'js.HTMLInputElement', '<input type="text" data-name="#name#" value="#name#">'),
#     _comp('button', 'js.HTMLButtonElement', '<button data-name="#name#">#name#</button>'),
#     _comp('textarea', 'js.HTMLTextAreaElement', '<textarea data-name="#name#">#name#</textarea>'),
#     _comp('select', 'js.HTMLSelectElement',
#           '<select data-name="#name#"><option>#name#</option></select>'),
#     _comp('div', 'js.HTMLDivElement', '<div data-name="#name#">#name#</div>'),
#     _comp('p', 'js.HTMLParagraphElement', '<p data-name="#name#">#name#</p>'),
#     _comp('h1', 'js.HTMLHeadingElement', '<h1 data-name="#name#">#name#</h1>'),
#     _comp('h2', 'js.HTMLHeadingElement', '<h2 data-name="#name#">#name#</h2>'),
#     _comp('h3', 'js.HTMLHeadingElement', '<h3 data-name="#name#">#name#</h3>'),
#     _comp('a', 'js.HTMLAnchorElement', '<a href="#" data-name="#name#">#name#</a>'),
#     _comp('img', 'js.HTMLImageElement', '<img src="#" alt="#name#" data-name="#name#">'),
#     _comp('ul', 'js.HTMLUListElement', '<ul data-name="#name#"><li>#name#</li></ul>'),
#     _comp('ol', 'js.HTMLOListElement', '<ol data-name="#name#"><li>#name#</li></ol>'),
#     _comp('li', 'js.HTMLLIElement', '<li data-name="#name#">#name#</li>'),
#     _comp('table', 'js.HTMLTableElement', '<table data-name="#name#"><tr><td>#name#</td></tr></table>'),
#     _comp('form', 'js.HTMLFormElement', '<form data-name="#name#">#name#</form>'),
#     _comp('label', 'js.HTMLLabelElement', '<label data-name="#name#">#name#</label>'),
#
# ]
