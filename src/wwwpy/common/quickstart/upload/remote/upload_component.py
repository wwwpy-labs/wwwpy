import asyncio
import base64
import logging

import js
import wwwpy.remote.component as wpc
from pyodide.ffi import create_proxy, JsException
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)


class UploadComponent(wpc.Component, tag_name='wwwpy-quickstart-upload'):
    file_input: js.HTMLInputElement = wpc.element()
    uploads: js.HTMLElement = wpc.element()

    @property
    def multiple(self) -> bool:
        return self.file_input.hasAttribute('multiple')

    @multiple.setter
    def multiple(self, value: bool):
        self.file_input.toggleAttribute('multiple', value)

    def root_element(self):
        return self.shadow

    def init_component(self):
        self.shadow = self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.shadow.innerHTML = """
<input data-name="file_input" placeholder="input1" type="file" multiple>
<div data-name="uploads"></div>
        """

    async def file_input__change(self, event):
        files = self.file_input.files
        for file in files:
            progress = UploadProgressComponent()
            self.uploads.appendChild(progress.element)
            asyncio.create_task(progress.upload(file))
        self.file_input.value = ''

class UploadProgressComponent(wpc.Component):
    file_input: js.HTMLInputElement = wpc.element()
    progress: js.HTMLProgressElement = wpc.element()
    progress_label: js.HTMLLabelElement = wpc.element()
    label: js.HTMLInputElement = wpc.element()

    def init_component(self):
        # language=html
        self.element.innerHTML = """
<div data-name="progress_label" style='padding: 0.5em'>
    <progress data-name="progress"></progress>
    &nbsp;<span data-name="label"></span>
</div>"""

    async def upload(self, file: js.File, chunk_size: int = pow(2, 18)):
        def set_label(text):
            self.label.textContent = f'{file.name}: {text}'

        logger.info(f'upload file: {file.name} {file.size} {file.type}')
        set_label('uploading...')
        try:
            from server import rpc
            await rpc.upload_init(file.name, file.size)
            offset = 0
            total_size = file.size
            self.progress.max = total_size
            while offset < total_size:
                chunk: js.Blob = file.slice(offset, offset + chunk_size)
                array_buffer = await self._read_chunk(chunk)
                # Process the chunk_text as needed
                logger.info(f'offset={offset}')
                b64str = base64.b64encode(array_buffer.to_py()).decode()
                await rpc.upload_append(file.name, b64str)
                offset += chunk_size
                self.progress.value = offset
                # percentage with two decimals
                percentage = round(offset / total_size * 100, 2)
                set_label(f'{percentage}%')
            set_label('upload completed')
            self.progress.value = total_size
            await asyncio.sleep(3)
            self.element.remove()
        except Exception as e:
            set_label(f'error: {e}')
            logger.exception(e)
            raise

    async def _read_chunk(self, blob: js.Blob) -> str:
        future: asyncio.Future = asyncio.Future()

        def onload(event):
            future.set_result(reader.result)

        def onerror(event):
            future.set_exception(JsException(reader.error))

        reader: js.FileReader = js.FileReader.new()
        reader.onload = create_proxy(onload)
        reader.onerror = create_proxy(onerror)
        reader.readAsArrayBuffer(blob)

        return await future
