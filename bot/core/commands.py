from collections.abc import Generator


class Commands:
    def as_list(self) -> Generator[str]:
        for attribute in dir(self):
            if attribute.startswith("__"):
                continue
            if attribute == "as_list":
                continue
            yield attribute
