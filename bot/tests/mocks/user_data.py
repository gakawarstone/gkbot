from typing import ClassVar
from typing import Any


class MockedUserDataExtension:
    __user_data: ClassVar[dict[str, Any]] = {}

    @property
    def user_data(self) -> dict[str, Any]:
        return self.__user_data
