from typing import List

from wwwpy.common.designer.el_common import ad_value, ad_disabled, ad_readonly, ad_autofocus, ad_required, \
    ad_placeholder, ad_name, ed_click, ed_dblclick, ed_input, ed_change, _insert_common_to_all
from wwwpy.common.designer.element_library import ElementDef, Help, AttributeDef, NamedListMap


def _standard_elements_def() -> List[ElementDef]:
    res = [
        ElementDef(
            'button', 'js.HTMLButtonElement',
            help=Help('A clickable button.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/button'),
            attributes=[
                AttributeDef('type', Help('The type of the button.', ''),
                             values=['submit', 'reset', 'button'], default_value='button'),
                ad_value,
                ad_disabled,
                ad_autofocus,
            ],
            events=[ed_click, ed_dblclick],
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
                ad_value,
                ad_placeholder,
                ad_disabled,
                ad_readonly,
                ad_required,
                ad_name,
                AttributeDef('min', Help('The minimum value of the input field.', '')),
                AttributeDef('max', Help('The maximum value of the input field.', '')),
                AttributeDef('step', Help('The legal number intervals for the input field.', '')),
                AttributeDef('pattern', Help('A regular expression that the input\'s value is checked against.', '')),
                AttributeDef('autocomplete', Help(
                    'Lets web developers specify what if any permission the user agent has to provide automated assistance in filling out form field values, as well as guidance to the browser as to the type of information expected in the field.',
                    ''),
                             values=['on', 'off']),
                AttributeDef('autocapitalize', Help(
                    'Controls whether inputted text is automatically capitalized and, if so, in what manner.', ''),
                             values=['on', 'off']),
                ad_autofocus,
                AttributeDef('checked', Help('Whether the control is checked.', ''), boolean=True),
                AttributeDef('multiple', Help('Whether the user is allowed to enter more than one value.', ''),
                             boolean=True),

            ],
            events=[ed_input, ed_click, ed_change]
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
                ad_disabled,
                ad_readonly,
                ad_required,
                ad_placeholder,
                ad_autofocus,
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
                ad_name,
            ],
            events=[ed_input, ed_change, ],
        ),
        ElementDef(
            'div', 'js.HTMLDivElement',
            help=Help('A generic container element.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div')
        ),
        ElementDef(
            'br', 'js.HTMLBRElement',
            help=Help('It produces a line break in text (carriage-return).',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/br')
        ),
        ElementDef(
            'progress', 'js.HTMLProgressElement',
            help=Help('A progress bar.',
                      'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/progress'),
            attributes=[
                AttributeDef('value', Help('The current value of the progress bar.', '')),
                AttributeDef('max', Help('The maximum value of the progress bar.', '')),
            ],
            events=[ed_click, ]
        ),
        ElementDef(
            'select', 'js.HTMLSelectElement',
            help=Help(
                'A control that provides a menu of options.',
                'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/select'
            ),
            attributes=[
                ad_name,
                ad_disabled,
                AttributeDef(
                    'multiple',
                    Help('Whether multiple options can be selected.', ''),
                    boolean=True
                ),
                ad_required,
                AttributeDef(
                    'size',
                    Help('Number of visible options.', ''),
                    default_value='1'
                ),
                ad_autofocus,
                AttributeDef(
                    'form',
                    Help('The form element that the select is associated with (its id).', '')
                ),
            ],
            events=[ed_change, ed_input],

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
            events=NamedListMap([ed_click, ]),
        ),
        ElementDef('a', 'js.HTMLAnchorElement',
                   help=Help('A hyperlink.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a'),
                   attributes=[AttributeDef('href', Help('The URL of the hyperlink.',
                                                         'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/a'))])
        ,
        ElementDef('img', 'js.HTMLImageElement',
                   help=Help('An image.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img'), attributes=[
                AttributeDef('src', Help('The source URL of the image.',
                                         'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img')),
                AttributeDef('alt', Help('Alternative text for the image.',
                                         'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img'))])
        ,
        ElementDef('option', 'js.HTMLOptionElement', help=Help('An option in a select list.',
                                                               'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/option'),
                   attributes=[AttributeDef('value', Help('The value of the option.',
                                                          'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/option')),
                               AttributeDef('disabled', Help('Disables the option.',
                                                             'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/option'),
                                            boolean=True)])
        ,
        ElementDef('form', 'js.HTMLFormElement',
                   help=Help('A form.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form'), attributes=[
                AttributeDef('action', Help('The URL to process the form submission.',
                                            'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form')),
                AttributeDef('method', Help('The HTTP method for form submission.',
                                            'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/form'),
                             values=['get', 'post'], default_value='get')])
        ,
        ElementDef('script', 'js.HTMLScriptElement',
                   help=Help('A script.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script'),
                   attributes=[AttributeDef('type', Help('The MIME type of the script.',
                                                         'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script'))])
        ,
        ElementDef('pre', 'js.HTMLPreElement',
                   help=Help('Preformatted text.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/pre'),
                   events=[ed_click, ed_dblclick])
        ,
        ElementDef('code', 'js.HTMLElement',
                   help=Help('Computer code.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/code'),
                   events=[ed_click, ed_dblclick])

    ]

    _add_additional(res)

    for r in res:
        r.gen_html = _generateHtml

    _insert_common_to_all(res)
    return res


_element_additional = [
    # tag_name, python_type, description, url
    ('h1', 'js.HTMLHeadingElement', 'A top-level heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h1'),
    ('h2', 'js.HTMLHeadingElement', 'A level-2 heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h2'),
    ('h3', 'js.HTMLHeadingElement', 'A level-3 heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h3'),
    ('h4', 'js.HTMLHeadingElement', 'A level-4 heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h4'),
    ('h5', 'js.HTMLHeadingElement', 'A level-5 heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h5'),
    ('h6', 'js.HTMLHeadingElement', 'A level-6 heading.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/h6'),
    ('p', 'js.HTMLParagraphElement', 'A paragraph.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/p'),
    ('span', 'js.HTMLSpanElement', 'A generic inline container.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/span'),
    ('strong', 'js.HTMLElement', 'A strong emphasis.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/strong'),
    ('em', 'js.HTMLElement', 'An emphasized text.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/em'),
    ('ul', 'js.HTMLUListElement', 'An unordered list.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/ul'),
    ('ol', 'js.HTMLOListElement', 'An ordered list.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/ol'),
    ('li', 'js.HTMLLIElement', 'A list item.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/li'),
    ('table', 'js.HTMLTableElement', 'A table.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/table'),
    ('thead', 'js.HTMLTableSectionElement', 'A table header.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/thead'),
    ('tbody', 'js.HTMLTableSectionElement', 'A table body.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/tbody'),
    ('tr', 'js.HTMLTableRowElement', 'A table row.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/tr'),
    ('th', 'js.HTMLTableCellElement', 'A table header cell.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/th'),
    ('td', 'js.HTMLTableCellElement', 'A table data cell.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/td'),
    ('label', 'js.HTMLLabelElement', 'A label.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/label'),
    ('optgroup', 'js.HTMLOptGroupElement', 'A group of options in a select list.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/optgroup'),
    ('hr', 'js.HTMLHRElement', 'A thematic break.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/hr'),
    ('nav', 'js.HTMLElement', 'A navigation section.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/nav'),
    ('header', 'js.HTMLElement', 'A header section.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/header'),
    ('footer', 'js.HTMLElement', 'A footer section.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/footer'),
    ('main', 'js.HTMLElement', 'A main section.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/main'),
    ('section', 'js.HTMLElement', 'A section.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/section'),
    ('article', 'js.HTMLElement', 'An article.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/article'),
    ('aside', 'js.HTMLElement', 'An aside section.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/aside'),
    ('figure', 'js.HTMLFigureElement', 'A figure.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/figure'),
    ('figcaption', 'js.HTMLElement', 'A figure caption.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/figcaption'),
    ('details', 'js.HTMLDetailsElement', 'A details section.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details'),
    ('summary', 'js.HTMLElement', 'A summary.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/summary'),
    ('video', 'js.HTMLVideoElement', 'A video.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video'),
    ('audio', 'js.HTMLAudioElement', 'An audio.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/audio'),
    ('source', 'js.HTMLSourceElement', 'A source.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/source'),
    ('canvas', 'js.HTMLCanvasElement', 'A canvas.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/canvas'),
    (
        'iframe', 'js.HTMLIFrameElement', 'An iframe.',
        'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/iframe'),
    ('embed', 'js.HTMLEmbedElement', 'An embed.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/embed'),
    (
        'object', 'js.HTMLObjectElement', 'An object.',
        'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/object'),
    ('map', 'js.HTMLMapElement', 'A map.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/map'),
    ('style', 'js.HTMLStyleElement', 'A style.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/style'),
    ('title', 'js.HTMLTitleElement', 'A title.', 'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/title'),
    ('template', 'js.HTMLTemplateElement', 'A template.',
     'https://developer.mozilla.org/en-US/docs/Web/HTML/Element/template'),
]


def _add_additional(elements: List[ElementDef]):
    already_present = {e.tag_name for e in elements}
    for tag_name, python_type, description, url in _element_additional:
        if tag_name not in already_present:
            elements.append(ElementDef(tag_name, python_type, help=Help(description, url)))


def _generateHtml(element_def: ElementDef, name: str) -> str:
    tag_name = element_def.tag_name

    def _def(placeHolder=False, add='', inner=None):
        def inner_func():
            pl = '' if not placeHolder else f' placeholder="{name}"'
            add1 = '' if not add else f' {add}'
            content = name if inner is None else inner
            return f'<{tag_name} data-name="{name}"{pl}{add1}>{content}</{tag_name}>'

        return inner_func

    func = {
        'button': _def(),
        'label': _def(),
        'div': _def(),
        'br': lambda: '<br>',
        'input': lambda: f'<input data-name="{name}" placeholder="{name}">',
        'img': lambda: f'<img data-name="{name}" src="https://images.unsplash.com/photo-1517331156700-3c241d2b4d83?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=90" alt="{name}">',
        'progress': lambda: f'<progress data-name="{name}" value="70" max="100">70%</progress>',
        'textarea': _def(placeHolder=True, inner='', add='rows="6" wrap="off" style="width: 100%"'),
        'select': _def(inner='''
            <option value="option1">Option 1</option>
            <option value="option2">Option 2</option>
            <option value="option3">Option 3</option>
        '''),
        'meter': _def(add='value="0.85" min="0" max="1" low="0.3" high="0.7" optimum="0.8"'),
        'span': _def(),
        'a': _def(),
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
