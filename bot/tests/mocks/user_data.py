from typing import ClassVar

from middlewares.data import UserData


class MockedUserDataExtension:
    __user_data: ClassVar[UserData] = {"delete_queue": []}

    @property
    def user_data(self) -> UserData:
        return self.__user_data
