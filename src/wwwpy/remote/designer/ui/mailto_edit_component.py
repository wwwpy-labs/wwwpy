import logging
from dataclasses import dataclass

import js
import wwwpy.remote.component as wpc
from wwwpy.common.state import _restore

from .mailto_component import MailtoComponent

logger = logging.getLogger(__name__)


@dataclass
class State:
    recipient: str = ''
    subject: str = ''
    body: str = ''
    text_content: str = ''


class MailtoEditComponent(wpc.Component):
    _recipient: js.HTMLElement = wpc.element()
    _subject: js.HTMLElement = wpc.element()
    _body: js.HTMLElement = wpc.element()
    _text_content: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<h1>MailtoEditComponent</h1>
<sl-input data-name="_recipient" placeholder="Recipient" label="Recipient" ></sl-input>
<sl-input data-name="_subject" placeholder="Subject" label="Subject"></sl-input>
<sl-textarea data-name="_body" placeholder="Body" label="Body">slTextarea1</sl-textarea>
<sl-input data-name="_text_content" placeholder="Link text content" label="Link text content"></sl-input>
<br>
        """
        self.state = _restore(State)
        self._recipient.value = self.state.recipient
        self._subject.value = self.state.subject
        self._body.value = self.state.body
        self._text_content.value = self.state.text_content

        target = MailtoComponent()
        self.element.append(target.element)
        self.target = target
        self._update()

    def _update(self):
        self.state.recipient = self._recipient.value
        self.state.subject = self._subject.value
        self.state.body = self._body.value
        self.state.text_content = self._text_content.value

        self.target.recipient = self._recipient.value
        self.target.body = self._body.value
        self.target.subject = 'add_component error report'
        self.target.text_content = self._text_content.value

    async def _recipient__sl_input(self, event):
        self._update()

    async def _subject__sl_input(self, event):
        self._update()

    async def _body__sl_input(self, event):
        self._update()

    async def _text_content__sl_input(self, event):
        self._update()

    async def _text_content__click(self, event):
        js.console.log('handler _text_content__click event =', event)
