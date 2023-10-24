from typing import Generator


class Commands:
    def as_list(self) -> Generator[str, None, None]:
        for attribute in dir(self):
            if attribute.startswith('__'):
                continue
            if attribute == 'as_list':
                continue
            yield attribute
