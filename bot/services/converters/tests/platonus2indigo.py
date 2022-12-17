from typing import Generator

from utils.chunks import chunks
from .generators.indigo import IndigoGenerator
from .parsers.platonus import PlatonusParser


class Platonus2Indigo:
    @classmethod
    def get_lines_with_max_questions(
            cls, data: list[str], max_questions: int
    ) -> Generator[list[str], None, None]:
        questions = PlatonusParser.parse_lines(data)
        for chunk in chunks(questions, max_questions):
            yield IndigoGenerator.generate_lines(chunk)
