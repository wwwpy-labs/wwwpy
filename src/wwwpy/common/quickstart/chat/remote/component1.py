import logging

import js
from common import name

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)

class Component1(wpc.Component, tag_name='component-1'):
    slInput1: js.HTMLElement = wpc.element()
    slTextarea1: js.HTMLElement = wpc.element()
    slSwitch1: js.HTMLElement = wpc.element()
    nickname: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<style> * { margin: 0.25em; } </style>
<h2>You are: <span data-name="nickname"></span></h2>
<sl-switch data-name="slSwitch1" checked>Allow empty messages</sl-switch>
<sl-input data-name="slInput1" placeholder="Message"></sl-input>
<sl-button data-name="slButton1">Send<sl-icon slot="suffix" name="send"></sl-icon></sl-button>
<sl-textarea data-name="slTextarea1" placeholder="No messages yet" rows="10">Messages...</sl-textarea>
"""
        local_storage_key = 'wwwpy.userspace.chat.nickname'
        nick = js.window.localStorage.getItem(local_storage_key)
        if not nick:
            nick = name.generate_name()
            js.window.localStorage.setItem(local_storage_key, nick)
        self.nickname.textContent = nick

        def new_message(message):
            self.slTextarea1.value += message + '\n'
            self.slTextarea1.scrollPosition(dict_to_js({'top': 999999999}))

        import remote.rpc
        remote.rpc.messages_listeners.append(new_message)

    async def slButton1__click(self, event):
        logger.debug('handler slButton1__click')
        self._set_error('')
        try:
            message = self.slInput1.value.strip()
            if not message:
                if not self.slSwitch1.checked:
                    self._set_error('Please enter a message')
                    return
                message = 'Empty message'

            import server.rpc
            await server.rpc.send_message_to_all(self.nickname.innerText + ': ' + message)
            self.slInput1.value = ''
            self._set_error('')
        except Exception as e:
            self._set_error('Issues sending message... ' + str(e))

    def _set_error(self, msg):
        self.slInput1.setCustomValidity(msg)
        self.slInput1.reportValidity()
