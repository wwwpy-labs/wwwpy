import inspect
import logging

import js
from pyodide.ffi import create_proxy

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)


class LoggerLevelsComponent(wpc.Component):
    _ta_log: js.HTMLTextAreaElement = wpc.element()
    _title: js.HTMLDivElement = wpc.element()
    _row_container: js.HTMLDivElement = wpc.element()
    _search: js.HTMLInputElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div data-name="_title">_title</div>
<input data-name="_search" placeholder="Filter by logger name">
<div data-name="_row_container"><br></div>  

<label>Component logs:</label>
<textarea data-name="_ta_log" placeholder="textarea1" rows="8" wrap="off" style="width: 98%"></textarea> 
"""
        self._list_all_logger()

    def _list_all_logger(self):
        import logging

        items = [(n, l) for n, l in logging.root.manager.loggerDict.items() if isinstance(l, logging.Logger)]
        # items.sort(key=lambda x: (x[1].level, x[0]), reverse=True)  # sort by logger name
        items.sort(key=lambda t: - t[1].level)
        items.sort(key=lambda t: t[0].lower())
        logger_counter = 0
        self._row_container.innerHTML = ''  # clear previous rows
        for name, logger in items:
            if not self._filter_accept(name):
                continue
            logger_counter += 1
            level_name = '' if logger.level == logging.NOTSET else logging.getLevelName(logger.level)
            row = LogConfRow()
            row.logger_name = name
            row.level_select = level_name
            self._row_container.appendChild(row.element)
        self._title.innerText = f'Found {logger_counter} loggers'
        self._log(self._title.innerText)

        # scroll to the top of the log area
        # self._ta_log.scrollTop = 0

    def _log(self, message):
        if not isinstance(message, str):
            message = str(message)
        self._ta_log.value += f"{message}\n"
        self._ta_log.scrollTop = self._ta_log.scrollHeight

    async def _row_container__input_row(self, event):
        row: LogConfRow = event.detail.row
        logging.getLogger(row.logger_name).setLevel(row.level_select)
        msg = f'{row.level_select:<8} {row.logger_name}'
        logger.debug(msg)
        self._log(msg)

    async def _search__input(self, event):
        logger.debug(f'{inspect.currentframe().f_code.co_name} event fired %s', event)
        self._list_all_logger()

    def _filter_accept(self, logger_name: str) -> bool:
        s = self._search.value.lower()
        if not s:
            return True
        ln = logger_name.lower()
        if ' ' in s:
            if s.strip() == ln:
                return True
            return False
        if s in ln:
            return True
        return False


class LogConfRow(wpc.Component):
    _level_select: js.HTMLSelectElement = wpc.element()
    _logger_name: js.HTMLSpanElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """       
<div>         
    <select data-name="_level_select"></select>
    <span data-name="_logger_name">_logger_name</span>
</div>
"""

        self._level_select.innerHTML = ''
        items = list(logging.getLevelNamesMapping().items())
        items.sort(key=lambda x: x[1])
        for name, level in items:
            option = js.document.createElement('option')
            option.value = name
            if level != logging.NOTSET:
                option.innerText = name
            self._level_select.appendChild(option)

    @property
    def level_select(self) -> str:
        return self._level_select.value

    @level_select.setter
    def level_select(self, level_name: str):
        self._level_select.value = level_name

    @property
    def logger_name(self) -> str:
        return self._logger_name.innerText

    @logger_name.setter
    def logger_name(self, name: str):
        self._logger_name.innerText = name

    async def _level_select__input(self, event):
        logger.debug(f'{inspect.currentframe().f_code.co_name} event fired %s', event)
        init = dict_to_js({'bubbles': True, 'detail': {'row': self}})
        self.element.dispatchEvent(js.CustomEvent.new('input-row', init))
