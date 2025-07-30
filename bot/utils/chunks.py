from typing import Generator


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def split_str_into_chunks(text: str, size: int = 4000) -> Generator[str, None, None]:
    words = text.split()

    if not words:
        return

    current_chunk: list[str] = []
    current_length = 0
    for word in words:
        if not current_chunk:
            current_chunk.append(word)
            current_length = len(word)

        elif current_length + 1 + len(word) > size:
            yield " ".join(current_chunk)
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += 1 + len(word)

    if current_chunk:
        yield " ".join(current_chunk)
