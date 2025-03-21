import asyncio
import base64
import logging

import js
from pyodide.ffi import create_proxy, JsException

import wwwpy.remote.component as wpc
from wwwpy.remote import dict_to_js

logger = logging.getLogger(__name__)


class UploadComponent(wpc.Component, tag_name='wwwpy-quickstart-upload'):
    file_input: js.HTMLInputElement = wpc.element()
    uploads: js.HTMLElement = wpc.element()
    dropzone: js.HTMLElement = wpc.element()  # New element for drop zone

    @property
    def multiple(self) -> bool:
        return self.file_input.hasAttribute('multiple')

    @multiple.setter
    def multiple(self, value: bool):
        self.file_input.toggleAttribute('multiple', value)

    def init_component(self):
        self.element.attachShadow(dict_to_js({'mode': 'open'}))
        # language=html
        self.element.shadowRoot.innerHTML = """
<div data-name="dropzone" style="border: 2px dashed #ccc; padding: 20px; text-align: center; margin-bottom: 10px; cursor: pointer;">
    <p>Drag and drop files here or</p>
    <input data-name="file_input" placeholder="input1" type="file" multiple style="display: inline-block;">
</div>
<div data-name="uploads"></div>
        """

    def dropzone__dragover(self, event):
        # Prevent default to allow drop
        event.preventDefault()
        event.stopPropagation()
        # Add visual feedback
        self.dropzone.style.borderColor = '#0099ff'
        self.dropzone.style.backgroundColor = 'rgba(0, 153, 255, 0.1)'

    def dropzone__dragleave(self, event):
        event.preventDefault()
        event.stopPropagation()
        # Reset visual feedback
        self.dropzone.style.borderColor = '#ccc'
        self.dropzone.style.backgroundColor = 'transparent'

    def dropzone__drop(self, event):
        event.preventDefault()
        event.stopPropagation()
        # Reset visual feedback
        self.dropzone.style.borderColor = '#ccc'
        self.dropzone.style.backgroundColor = 'transparent'

        # Get files from the drop event
        files = event.dataTransfer.files
        self._process_files(files)

    def dropzone__click(self, event):
        # If they click the drop zone but not on the input, trigger the file input
        if event.target != self.file_input:
            self.file_input.click()

    def _process_files(self, files):
        # Process the files just like in the change event
        for file in files:
            progress = UploadProgressComponent()
            self.uploads.appendChild(progress.element)
            asyncio.create_task(progress.upload(file))

    async def file_input__change(self, event):
        files = self.file_input.files
        self._process_files(files)
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
            fade_delay = 3
            self.element.style.opacity = '1'
            self.element.style.transition = f'opacity {fade_delay}s'
            self.element.style.opacity = '0'
            await asyncio.sleep(fade_delay)
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
