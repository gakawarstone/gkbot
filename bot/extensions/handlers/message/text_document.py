from aiogram.types import BufferedInputFile, Message


async def send_text_document(
    message: Message, lines: list[str], file_name: str
) -> Message:
    document = BufferedInputFile("".join(lines).encode("utf-8"), file_name)
    return await message.answer_document(document)
