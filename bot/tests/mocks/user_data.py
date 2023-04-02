class MockedUserDataExtension:
    __user_data = {}

    @property
    def user_data(self) -> dict:
        return self.__user_data
