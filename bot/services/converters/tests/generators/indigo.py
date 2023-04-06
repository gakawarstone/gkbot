from ..types import Question


class IndigoGenerator:
    @classmethod
    def generate_lines(cls, questions: list[Question]) -> list[str]:
        lines = []
        for question in questions:
            lines += cls._question_to_lines(question)
        return lines

    @staticmethod
    def _question_to_lines(question: Question) -> list[str]:
        lines = []
        lines.append(question.title + '\n')
        for choice in question.choices:
            line = choice.text
            if choice.is_correct:
                line = '*' + line
            lines.append(line + '\n')
        lines.append('\n')
        return lines
