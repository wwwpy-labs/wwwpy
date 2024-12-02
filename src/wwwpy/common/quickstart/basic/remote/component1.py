import wwwpy.remote.component as wpc
import js

import logging

logger = logging.getLogger(__name__)


class Component1(wpc.Component, tag_name='component-1'):

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div>component-1</div>
"""
