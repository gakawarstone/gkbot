import re
from io import BytesIO
from typing import Any

from aiogram.types import BufferedInputFile

from ui.static import Images
from extensions.handlers.message.file_extension import (
    FileHandlerExtension,
    NoFileException,
)
from ._states import FSM


class SortFileHandler(FileHandlerExtension):
    async def handle(self) -> Any:
        await self.state.set_state(FSM.finish)
        await self.event.delete()

        try:
            buffer = await self.document_io
            text = buffer.getvalue().decode("utf-8")
            lines = text.splitlines(keepends=True)
            sorted_lines = sorted(lines, key=self.get_line_date_as_int)
            caption = "Вот твой отсортированный документ 👇"
            await self.event.answer_photo(
                await Images.sorted_documents.as_input_file(), caption=caption
            )
            await self._send_sorted_file(sorted_lines, self.event.document.file_name)
        except NoFileException:
            await self.state.set_state(FSM.sort_file)
            await self.event.answer("Отправьте файл")

    def get_line_date_as_int(self, line):
        year_pattern = r"\d{4}\."
        date_pattern = r"(\d{2})\.(\d{2})\.(\d{4})"

        date_matches = re.findall(date_pattern, line)
        year_matches = re.findall(year_pattern, line)

        if year_matches:
            return int(year_matches[-1][:-1] + "0000")

        if date_matches:
            day, month, year = date_matches[0]
            return int(year + month + day)

        return 99999999

    async def _send_sorted_file(self, lines: list[str], file_name: str) -> None:
        output_file = BytesIO()
        [output_file.write(line.encode()) for line in lines]
        file = BufferedInputFile(output_file.getvalue(), file_name)
        await self.event.answer_document(file)
