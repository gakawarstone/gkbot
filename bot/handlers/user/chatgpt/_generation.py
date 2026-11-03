from asyncio import Task
from dataclasses import dataclass

from aiogram import Bot
from aiogram.enums import ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import MessageGenerationStopped

GenerationKey = tuple[int, int, int | None, int]


@dataclass
class ActiveGeneration:
    task: Task[str]
    state: FSMContext
    stopped: bool = False


# Stop updates have no from_user and therefore no injected FSMContext.
# Keep the source context and task until generation and cleanup have finished.
active_generations: dict[GenerationKey, ActiveGeneration] = {}


async def stop_generation(event: MessageGenerationStopped, bot: Bot) -> None:
    if event.chat.type != ChatType.PRIVATE:
        return
    key = (bot.id, event.chat.id, event.message_thread_id, event.draft_id)
    generation = active_generations.get(key)
    if generation and not generation.stopped and not generation.task.done():
        generation.stopped = True
        generation.task.cancel()
