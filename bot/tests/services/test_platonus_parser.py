from services.converters.tests.parsers.platonus import PlatonusParser
from services.converters.tests.types import Choice, Question


def test_last_question_without_trailing_blank_line() -> None:
    lines = [
        "<question>First question",
        "<variant>First answer",
        "<variant>First alternative",
        "<question>Last question",
        "<variant>Last answer",
        "<variant>Last alternative",
    ]

    assert PlatonusParser.parse_lines(lines) == [
        Question(
            "First question",
            [Choice("First answer", True), Choice("First alternative", False)],
        ),
        Question(
            "Last question",
            [Choice("Last answer", True), Choice("Last alternative", False)],
        ),
    ]
