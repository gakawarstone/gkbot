import re
from typing import Any

from ui.static import Images
from extensions.handlers.message.file_extension import (
    FileHandlerExtension,
    NoFileException,
)
from extensions.handlers.message.text_document import send_text_document
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
            file_name = getattr(self.event.document, "file_name", None)
            if file_name is None:
                raise ValueError("document.file_name is None")
            await send_text_document(self.event, sorted_lines, file_name)
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
