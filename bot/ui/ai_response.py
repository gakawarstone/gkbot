from aiogram.utils.formatting import Text, sizeof

from extensions.handlers.message.markdown_render import parse_markdown, render_html

RESPONSE_MESSAGE_LIMIT = 1500


def split_response(markdown: str, limit: int = RESPONSE_MESSAGE_LIMIT) -> list[str]:
    """Split rendered text into HTML messages, bounded in UTF-16 code units.

    Telegram counts text after entity parsing. Clip entities for each message
    so code blocks and bold text remain valid even across message boundaries.
    The original Markdown is kept separately by the caller for chat history.
    """
    text, entities = parse_markdown(markdown).render()
    chunks = []
    offset = 0
    for chunk in split_text(text, limit):
        end = offset + sizeof(chunk)
        chunk_entities = [
            entity.model_copy(
                update={
                    "offset": max(entity.offset, offset) - offset,
                    "length": min(entity.offset + entity.length, end)
                    - max(entity.offset, offset),
                }
            )
            for entity in entities
            if entity.offset < end and entity.offset + entity.length > offset
        ]
        chunks.append(render_html(Text.from_entities(chunk, chunk_entities)))
        offset = end
    return chunks


def split_text(text: str, limit: int = RESPONSE_MESSAGE_LIMIT) -> list[str]:
    """Preserve every character, preferring paragraphs, lines, then spaces."""
    if limit < 2:
        raise ValueError("The message limit must fit any Unicode character")

    chunks = []
    start = 0
    while start < len(text):
        end = start
        size = 0
        while end < len(text) and size + sizeof(text[end]) <= limit:
            size += sizeof(text[end])
            end += 1

        if end < len(text):
            for separator in ("\n\n", "\n", " "):
                boundary = text.rfind(separator, start, end)
                if boundary >= start:
                    end = boundary + len(separator)
                    break
        chunks.append(text[start:end])
        start = end
    return chunks
