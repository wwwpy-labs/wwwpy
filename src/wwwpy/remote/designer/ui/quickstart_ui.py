import js
from pyodide.ffi import create_proxy
import asyncio
from wwwpy.common import quickstart
from wwwpy.remote.designer.ui.window_component import new_window, WindowComponent
from wwwpy.remote.designer.ui.searchable_list_1 import SearchableList1, Item
from wwwpy.server.designer import rpc


class QuickstartUI:

    def __init__(self):
        self.window: WindowComponent = new_window("Select a quickstart", closable=False)
        # self.window.set_size('300px', '300px')
        self.window.set_position('5px', '5px')
        cmp1 = SearchableList1()
        cmp1.root_element().style.color = 'white'
        quickstart_list = quickstart.quickstart_list()
        self.quickstart_list = quickstart_list
        cmp1.items = [Item(qs.title, qs.description, {'quickstart': qs}) for qs in quickstart_list]
        cmp1.placeholder = 'Search or select below...'
        self.window.element.append(cmp1.element)
        self.on_done = lambda *args: None

        cmp1.element.addEventListener('item-click', create_proxy(self._item_click_handler))

    def accept_quickstart(self, quickstart_name: str):
        self.window.element.remove()

        async def _notify_server():
            await rpc.quickstart_apply(quickstart_name)
            self.on_done(quickstart_name)

        asyncio.create_task(_notify_server())

    def _item_click_handler(self, event):
        item = event.detail
        assert isinstance(item, Item)
        self.accept_quickstart(item.values['quickstart'].name)


def create() -> QuickstartUI:
    return QuickstartUI()
