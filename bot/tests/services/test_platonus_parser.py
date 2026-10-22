import pytest

from services.converters.tests.parsers.platonus import PlatonusParser
from services.converters.tests.types import Choice, Question


@pytest.mark.parametrize("ending", ["", "\n", "\n\n"])
@pytest.mark.parametrize("question_count", [1, 2])
def test_last_question_without_trailing_blank_line(
    ending: str, question_count: int
) -> None:
    text = "\n".join(
        f"<question>Question {index}\n<variant>Correct\n<variant>Incorrect"
        for index in range(question_count)
    )

    assert PlatonusParser.parse_lines((text + ending).splitlines()) == [
        Question(
            f"Question {index}", [Choice("Correct", True), Choice("Incorrect", False)]
        )
        for index in range(question_count)
    ]
