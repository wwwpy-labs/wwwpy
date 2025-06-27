from __future__ import annotations

import asyncio

"""
This component is written to showcase the use of the `wwwpy` library for creating web components.
"""
import inspect

import wwwpy.remote.component as wpc
import \
    js  # generally we use `js.` to reference to the globals, so do not use `window.` as many of you might be used to.
import datetime
from pyodide.ffi import create_proxy

import logging

from wwwpy.remote import \
    dict_to_js  # when passing a python dictionary to a JS function, we need to convert it to a JS object

logger = logging.getLogger(__name__)


class Component1(wpc.Component, tag_name='component-1'):
    custom_attribute_1: str = wpc.attribute()
    """A custom attribute that can be set in the HTML tag. Beware that this is a string value 
    and has the same behavior as a normal HTML attribute. 
    There is no need to define the static list of attributes `observedAttributes`, the library will take care of it."""

    button1: js.HTMLButtonElement = wpc.element()
    textarea1: js.HTMLTextAreaElement = wpc.element()
    title_icon_1: TitleIconComponent = wpc.element()  # note that here we are telling wpc.element() to map the class type directly! this is handy because we can access all the properties and methods of the class.
    """The name here must match the 'data-name' in the html, so we will never use a 
    '-' for the name, in other words we will use valid python identifiers.
    
    Also take note that we use the Python class instead of a js.HTMLElement, you should prefer this declaration.
    If you want to attach an event handler to the element, you should prefer the autobinding (e.g., see the below method title_icon_1__title_close)
    so we don't need to use title_icon_1.element.addEventListener (and a manual create_proxy).
    
    """

    def init_component(self):
        f"""This method is to be intended as the constructor of the component.
        We cannot use __init__ because there is some dynamic binding between the javascript class instance and
        this class instance. This is also why we can reload the component without reloading the page (notably
        custom elements are do not support undefining them).
        """
        self.element.attachShadow(dict_to_js({
                                                 'mode': 'open'}))  # note the use of dict_to_js to convert the dictionary to a JS object, otherwise it will not work

        # note in the html that we use 'data-name' to assign the elements to the attributes.
        # We never use the 'id' attribute, because it is not a good practice to use it in web components.
        # language=html     # this comment is important, don't omit it, because it help the ide to colorize the html
        self.element.shadowRoot.innerHTML = """
<title-icon data-name='title_icon_1'>
    <div slot='title'>Select a file...</div>
</title-icon>
<button data-name="button1">button1</button>
<textarea data-name="textarea1" placeholder="textarea1" rows="6" wrap="off" style="width: 100%"></textarea>
"""
        self._resize_observer = None

    async def after_init_component(self):
        f"""This is called after init_component, it is a convenience method when async initialization 
        is needed. 
        """
        pass

    def connectedCallback(self):
        self._resize_observer = js.ResizeObserver.new(create_proxy(self._resize))
        self._resize_observer.observe(self.textarea1)

    def disconnectedCallback(self):
        self._resize_observer.disconnect()

    def adoptedCallback(self):
        """The standard callback when the component is moved in the DOM.
        I advise to not even define the method if you don't need it. (this goes for all the callbacks)"""

    def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
        pass

    async def _resize(self, entries, observer):
        if entries and len(entries) > 0:
            self._log(f'resize observed: {len(entries)} entries')

        # If you need to access specific properties of the entries:
        for entry in entries:
            content_rect = entry.contentRect
            self._log(f'New size: {content_rect.width}x{content_rect.height}')
            self._log(f'New size: {entry.target.clientWidth}x{entry.target.clientHeight}')

    async def button1__click(self, event):
        """By convention this will be attached to the button1 click event.
        So the separator is the name of the element, two underscores and the event name."""
        logger.debug(f'{inspect.currentframe().f_code.co_name} event fired %s', event)

        self._log('button 1 clicked')
        self.title_icon_1.flash()

    async def title_icon_1__title_close(self, event):
        self._log(f'title_icon_1__title_close event fired')

    def _log(self, message: str):
        # add to the textarea the datetime and the message, then scroll to the bottom
        now = datetime.datetime.now()

        # showcase the use of the elements made accessible by the wpc.element() decorator and 'data-name'
        self.textarea1.value += f'{now} - {message}\n'
        self.textarea1.scrollTop = self.textarea1.scrollHeight


class TitleIconComponent(wpc.Component, tag_name='title-icon'):
    _icon: js.HTMLImageElement = wpc.element()
    _close: js.HTMLButtonElement = wpc.element()

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<style>
    @keyframes flash {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    .flashing {
        animation: flash 0.3s ease-in-out infinite;
    }
</style>
<div style='display: flex; width: 100%'>
    <div style='flex: 1; text-align: center; font-size: 1.5rem'><slot name='title'></slot></div>
    <button data-name="_close" style='height: 1.5em; width: 1.5em; font-size: 1.2rem; line-height: 1; padding: 0 6px; border-radius: 50%'>×</button>
</div>
<hr>
<slot></slot>
"""

    async def _close__click(self, event):
        self.element.dispatchEvent(
            js.CustomEvent.new(  # note that this is a js.CustomEvent. Do not use window.CustomEvent.
                'title-close',
                # note that the auto-binding event handler is title_icon_1__title_close, so the dash is automatically converted to an underscore
                dict_to_js({'bubbles': True})

            )
        )

    def flash(self):
        # Add the flashing class
        self._close.classList.add('flashing')

        async def remove():
            await asyncio.sleep(2)
            self._close.classList.remove('flashing')

        asyncio.create_task(remove())
