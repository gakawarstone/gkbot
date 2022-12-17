from dataclasses import dataclass


@dataclass
class Choise:
    text: str
    is_correct: bool


@dataclass
class Question:
    title: str
    choises: list[Choise]
