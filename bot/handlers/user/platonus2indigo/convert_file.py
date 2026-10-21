from typing import Any

from extensions.handlers.message.file_extension import (
    FileHandlerExtension,
    NoFileException,
)
from extensions.handlers.message.text_document import send_text_document
from services.docx import DocxReader
from services.converters.tests.platonus2indigo import Platonus2Indigo
from ._states import FSM


class ConvertFileHandler(FileHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)

        try:
            text = DocxReader.read_str(await self.document_io)
        except NoFileException:
            await self.state.set_state(FSM.convert)
            return await self.event.answer("Отправьте файл")
        except ValueError:
            await self.state.set_state(FSM.convert)
            return await self.event.answer("Формат <b>.docx</b>")

        chunks = Platonus2Indigo.get_lines_with_max_questions(
            text.splitlines(), 25
        )  # FIXME hardcore
        for n, part in enumerate(chunks):
            await send_text_document(self.event, part, f"quest_{n}.txt")
