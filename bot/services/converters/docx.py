from io import BytesIO

import docx2txt
from zipfile import BadZipfile


class DocxConverter:
    @classmethod
    def convert_to_str(cls, file: BytesIO) -> str:
        try:
            lines = docx2txt.process(file).splitlines()
        except BadZipfile:
            raise ValueError
        stripped_lines = [l for n, l in enumerate(lines) if n % 2 == 0]
        return '\n'.join(stripped_lines)
