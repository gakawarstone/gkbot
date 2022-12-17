from typing import Any
from io import BytesIO

from aiogram.types import BufferedInputFile

from contrib.handlers.message.file_extension import FileHandlerExtension, NoFileException
from services.converters.docx import DocxConverter
from services.converters.tests.platonus2indigo import Platonus2Indigo
from ._states import FSM


class ConvertFileHandler(FileHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)

        try:
            text = DocxConverter.convert_to_str(await self.document_io)
        except NoFileException:
            await self.state.set_state(FSM.convert)
            await self.event.answer('Отправьте файл')
        except ValueError:
            await self.state.set_state(FSM.convert)
            await self.event.answer('Файл должен быть .docx')

        chunks = Platonus2Indigo.get_lines_with_max_questions(
            text.splitlines(), 25)  # FIXME hardcore
        for n, part in enumerate(chunks):
            await self._send_lines_file(part, f'quest_{n}')

    async def _send_lines_file(self, lines: list[str], file_name: str) -> None:
        output_file = BytesIO()
        [output_file.write(l.encode()) for l in lines]
        file = BufferedInputFile(output_file.getvalue(), file_name)
        await self.event.answer_document(file)