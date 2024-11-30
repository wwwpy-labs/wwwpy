import wwwpy.remote.component as wpc
import js

import logging
import urllib.parse

logger = logging.getLogger(__name__)


class MailtoComponent(wpc.Component):
    recipient: str = wpc.attribute()
    subject: str = wpc.attribute()
    body: str = wpc.attribute()
    text_content: str = wpc.attribute()
    target: js.HTMLElement = wpc.attribute()

    _link: js.HTMLElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """<a data-name="_link"></a>"""

        self._update_attributes()

    def attributeChangedCallback(self, name: str, oldValue: str, newValue: str):
        self._update_attributes()

    def connectedCallback(self):
        self._update_attributes()

    def _update_attributes(self):
        target = self.target if self.target else '_blank'
        recipient = self.recipient if self.recipient else 'foo@example.com'
        subject = self.subject if self.subject else 'subject not specified'
        body = self.body if self.body else ''
        text_content = self.text_content if self.text_content else f"Send Email to {recipient}"

        # make sure to encode the subject and body
        subject = urllib.parse.quote_plus(subject)
        body = urllib.parse.quote_plus(body)

        self._link.href = f"mailto:{recipient}?subject={subject}&body={body}"
        self._link.textContent = text_content
        self._link.target = target
