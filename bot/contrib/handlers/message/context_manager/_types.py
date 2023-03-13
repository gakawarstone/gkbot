from abc import ABC
from typing import NamedTuple
from dataclasses import dataclass


@dataclass
class Property:
    name: str
    type: type


@dataclass
class BaseContext:
    pass
