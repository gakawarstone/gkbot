from ..types import Question, Choise


class PlatonusParser:
    __question_tag = '<question>'
    __choise_tag = '<variant>'
    __tags = (__question_tag, __choise_tag)

    # FIXME: if end ofl line is not empty last question isn't append
    @classmethod
    def parse_lines(cls, lines: list[str]) -> list[Question]:
        questions = []
        question_buffer = []
        for line in lines:
            if line.strip().startswith(cls.__question_tag) and len(question_buffer) > 2:
                questions.append(cls._process_question_buffer(question_buffer))
                question_buffer = []
            if line.strip().startswith(cls.__tags):
                question_buffer.append(line.strip())
        if len(question_buffer) > 2:
            questions.append(cls._process_question_buffer(question_buffer))
        return questions

    @classmethod
    def _process_question_buffer(cls, question_buffer: list[str]) -> Question:
        if not cls._validate_question_buffer(question_buffer):
            raise ValueError
        question_buffer = cls._strip_question_buffer(question_buffer)

        title = question_buffer[0]
        choises = [Choise(l, False) for l in question_buffer[1:]]
        choises[0].is_correct = True
        return Question(title, choises)

    @classmethod
    def _validate_question_buffer(cls, question_buffer) -> bool:
        if not question_buffer[0].strip().startswith(cls.__question_tag):
            return False

        for line in question_buffer[1:]:
            if not line.strip().startswith(cls.__choise_tag):
                return False

        return True

    @classmethod
    def _strip_question_buffer(cls, question_buffer: list[str]) -> list[str]:
        tags = [cls.__question_tag, cls.__choise_tag]
        return [cls._remove_tags_from_line(l, tags) for l in question_buffer]

    @classmethod
    def _remove_tags_from_line(cls, line: str, tags: list[str]) -> str:
        for tag in tags:
            if line.startswith(tag):
                return line.split(tag)[1]
        else:
            return line
