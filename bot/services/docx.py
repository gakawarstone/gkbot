from io import BytesIO

import docx2txt  # type: ignore
from zipfile import BadZipfile


class DocxReader:
    @classmethod
    def read_str(cls, file: BytesIO) -> str:
        try:
            lines = docx2txt.process(file).splitlines()
        except BadZipfile:
            raise ValueError
        stripped_lines = [l for n, l in enumerate(lines) if n % 2 == 0]
        return "\n".join(stripped_lines)
