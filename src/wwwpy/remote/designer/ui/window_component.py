import wwwpy.remote.component as wpc
import js

import logging

from wwwpy.remote import dict_to_js
import asyncio

logger = logging.getLogger(__name__)


class WindowComponent(wpc.Component, tag_name='wwwpy-window'):
    window_div: wpc.HTMLElement = wpc.element()

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
<style>
.window {
  z-index: 100000;  
  border: 1px solid #d3d3d3;
  resize: both;  
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.window-title {
  padding: 10px;
  cursor: move;
  z-index: 1001;
  background-color: #2196F3;
  color: #fff;
}

.window-body {
  overflow: auto;
}
</style>        

<div data-name="window_div" class='window'>
    <div data-name="draggable_component_div" class='window-title' >
        <slot name='title' >slot=title</slot>
    </div>
    <div class='window-body'>
        <slot>slot=default</slot>
    </div>    
</div> 
"""


class Component1(wpc.Component, tag_name='component-1'):
    div1: js.HTMLElement = wpc.element()
    win1: WindowComponent = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """<span>component-1</span>
<hr>       
<wwwpy-window data-name='win1'>
<span slot='title'>titolo custom</span>
<div>cia</div>
<div data-name="div1"></div>
</wwwpy-window> 
        """

        async def add():
            for _ in range(10):
                self.div1.insertAdjacentHTML('beforeend', 'hello<br>')

        asyncio.create_task(add())

        self.win1.window_div.style.height = '130px'
        self.win1.window_div.style.width = '130px'
