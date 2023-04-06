from dataclasses import dataclass


@dataclass
class Choice:
    text: str
    is_correct: bool


@dataclass
class Question:
    title: str
    choices: list[Choice]
