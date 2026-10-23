
from .base_creator import BaseCreatorComponent


class BookCreatorComponent(BaseCreatorComponent):
    def __init__(
        self,
        title: str | None = None,
        author: str | None = None,
        num_of_pages: int | None = None,
        status_message: str | None = None,
    ) -> None:
        self.title = title
        self.author = author
        self.status_message = status_message
        self.num_of_pages = num_of_pages
        self._has_highlighted_property = False

        self.num_of_pages_str = None
        if num_of_pages:
            self.num_of_pages_str = str(num_of_pages)

    def render(self) -> str:
        text = "<u>Создатель книг 📕</u>\n"
        text += self._render_property(self.title, prefix="Название: ")
        text += self._render_property(self.author, prefix="Автор: ")
        text += self._render_property(self.num_of_pages_str, prefix="Кол-во страниц: ")
        text += self._render_if_exist(self.status_message)
        return text
