class BaseMarkup:
    prefix: str

    @classmethod
    def _gen_callback_data(cls, event: str, book_id: str):
        return f'{cls.prefix}:{event}:{book_id}'
