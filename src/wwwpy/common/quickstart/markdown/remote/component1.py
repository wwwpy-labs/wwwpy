import asyncio

import wwwpy.remote.component as wpc
import js

import logging

logger = logging.getLogger(__name__)


class Component1(wpc.Component, tag_name='component-1'):
    textarea1: js.HTMLTextAreaElement = wpc.element()
    div1: js.HTMLDivElement = wpc.element()
    title: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div data-name="title">Loading...</div>

<style>
.textarea1 {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    font-family: Arial, sans-serif;
    font-size: 14px;
    resize: vertical;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
</style>

<textarea data-name="textarea1" rows="7" class="textarea1"></textarea>
<hr>
<div data-name="div1"></div>

"""
        asyncio.ensure_future(self.after_init())

    async def after_init(self):
        logger.info('Component1 after_init')
        import micropip
        await micropip.install('markdown')
        import markdown
        # language=markdown
        self.title.innerHTML = markdown.markdown(f"""
# Component1
 - This is a simple component that uses a textarea and a div to render markdown.
 - This text itself is rendered using markdown.      
""")
        self.textarea1.value = js.localStorage.getItem('textarea1') or 'Write your _markdown_ here ...'
        self._render_markdown()

    async def textarea1__input(self, event):
        js.localStorage.setItem('textarea1', self.textarea1.value)
        self._render_markdown()

    def _render_markdown(self):
        import markdown
        self.div1.innerHTML = markdown.markdown(self.textarea1.value)
