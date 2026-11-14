from enum import StrEnum
from typing import Self


class Commands(StrEnum):
    description: str

    def __new__(cls, value: str, description: str) -> Self:
        command = str.__new__(cls, value)
        command._value_ = value
        command.description = description
        return command

    @classmethod
    def as_list(cls) -> list[str]:
        return sorted(command.value for command in cls)

    @classmethod
    def as_dict(cls) -> dict[str, str]:
        return {command.value: command.description for command in cls}
