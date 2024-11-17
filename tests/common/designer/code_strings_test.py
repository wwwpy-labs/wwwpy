from wwwpy.common.designer.code_strings import html_string_edit


def test_html_edit():
    for escape in ['"""', "'''"]:
        common_piece = f'''
import wwwpy.remote.component as wpc
# comment1
class MyElement(wpc.Component): # comment2
    btn1: HTMLButtonElement = wpc.element()
    def connectedCallback(self):        
        self.element.innerHTML = %s
        <div>my-element5 a</div>
        <button data-name='btn1'>list async tasks</button>
        ''' % escape

        original_source = common_piece + escape
        expected_source = common_piece + '''<button data-name='btn2'>list files in folder</button>''' + escape

        def manipulate_html(html):
            return html + "<button data-name='btn2'>list files in folder</button>"

        actual_source = html_string_edit(original_source, 'MyElement', manipulate_html)

        assert actual_source == expected_source


def test_html_edit__two_classes():
    common_piece = '''
import wwwpy.remote.component as wpc
class MyElement0(wpc.Component):
    def connectedCallback(self):        
        self.element.innerHTML = """untouched"""
        
class MyElement1(wpc.Component): 
    btn1: HTMLButtonElement = wpc.element()
    def connectedCallback(self):        
        self.element.innerHTML = """
        <div>my-element5 a</div>
        <button data-name='btn1'>list async tasks</button>
        '''

    original_source = common_piece + '"""'
    expected_source = common_piece + '''<button data-name='btn2'>list files in folder</button>"""'''

    def manipulate_html(html):
        return html + "<button data-name='btn2'>list files in folder</button>"

    actual_source = html_string_edit(original_source, 'MyElement1', manipulate_html)

    assert actual_source == expected_source


def test_html_from_source():
    source = '''
class Component1:
      def connectedCallback(self):        
        self.element.innerHTML = """<div>foo</div>"""
'''
    from wwwpy.common.designer.code_strings import html_from_source
    html = html_from_source(source, 'Component1')
    assert html == '<div>foo</div>'
