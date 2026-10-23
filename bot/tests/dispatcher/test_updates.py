from datetime import timedelta

import pytest
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.fsm.context import FSMContext
from aiogram.methods import AnswerInlineQuery, DeleteMessage, SendDocument, SendMessage
from aiogram.types import (
    BufferedInputFile,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from bot.handlers.button.delete_message import delete_message
from bot.handlers.inline.choose_list import send_choice
from bot.handlers.user.exit import exit_flow
from bot.handlers.user.reminder._states import FSM as ReminderFSM
from bot.handlers.user.reminder.start import InitHandler as ReminderInitHandler
from bot.handlers.user.timezone import FSM as TimezoneFSM
from bot.handlers.user.timezone import _set_timezone, init_timezone_set
from bot.handlers.user.tts._states import FSM as SpeechFSM
from bot.handlers.user.tts.init import InitHandler as SpeechInitHandler
from configs.commands import USER_COMMANDS
from services.timezone import UserDontHaveTimeZone
from tests.dispatcher.helpers import (
    ADMIN_IDS,
    USER_ID,
    DispatcherHarness,
    callback_update,
    inline_update,
    raw_message,
)
from ui.buttons.delete_message import deleteMessageButtonPrefix


async def test_command_and_fsm_input_use_registered_handlers(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.set_tz}")

    invocation = harness.invocations[0]
    assert invocation.callback is init_timezone_set
    assert isinstance(invocation.state, FSMContext)
    assert invocation.state_before is None
    assert invocation.data_before == {"delete_queue": []}
    assert await invocation.state.get_state() == TimezoneFSM.set_timezone.state
    harness.find_user.assert_awaited_once_with()
    harness.create_user.assert_awaited_once_with(
        user_id=USER_ID, user_name="Dispatcher Test"
    )
    assert len(harness.session.calls) == 1
    prompt = harness.session.calls[0]
    assert isinstance(prompt, SendMessage)
    assert prompt.chat_id == USER_ID
    assert prompt.text == "Введите число от -12 до +14:"

    await harness.message("3")

    next_invocation = harness.invocations[1]
    assert next_invocation.callback is _set_timezone
    assert next_invocation.state_before == TimezoneFSM.set_timezone.state
    assert next_invocation.user_data is invocation.user_data
    harness.set_timezone.assert_awaited_once_with(USER_ID, timedelta(hours=3))
    assert await invocation.state.get_state() == TimezoneFSM.finish.state
    assert len(harness.session.calls) == 2
    answer = harness.session.calls[1]
    assert isinstance(answer, SendMessage)
    assert answer.text == "Таймзона установлена"


async def test_invalid_fsm_input_retries_without_consuming_other_users(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.set_tz}")
    await harness.message("invalid offset")

    assert harness.invocations[-1].callback is _set_timezone
    assert await harness.state().get_state() == TimezoneFSM.set_timezone.state
    harness.set_timezone.assert_not_awaited()
    answer = harness.session.calls[-1]
    assert isinstance(answer, SendMessage)
    assert answer.text == "Таймзона должна быть от -12 до 14"
    assert len(harness.session.calls) == 2

    assert await harness.message("3", user_id=USER_ID + 1) is UNHANDLED
    assert await harness.state(USER_ID + 1).get_state() is None
    assert len(harness.invocations) == 2
    assert len(harness.session.calls) == 2


async def test_flagged_class_handler_receives_timezone_user_data_and_state(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.add_remind}")

    invocation = harness.invocations[0]
    assert invocation.callback is ReminderInitHandler
    assert isinstance(invocation.state, FSMContext)
    assert invocation.state_before is None
    assert invocation.data_before == {"delete_queue": [], "tz": timedelta(hours=3)}
    assert await invocation.state.get_state() == ReminderFSM.get_text.state
    harness.get_timezone.assert_awaited_once_with(USER_ID)
    assert len(harness.session.calls) == 2
    deletion, widget = harness.session.calls
    assert isinstance(deletion, DeleteMessage)
    assert (deletion.chat_id, deletion.message_id) == (USER_ID, 1)
    assert isinstance(widget, SendMessage)
    assert widget.chat_id == USER_ID
    assert "Текст" in widget.text
    assert invocation.user_data is not None
    assert invocation.user_data.get("message") is not None


async def test_missing_timezone_stops_before_handler_invocation(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    harness.get_timezone.side_effect = UserDontHaveTimeZone
    await harness.message(f"/{USER_COMMANDS.add_remind}")

    assert harness.invocations == []
    assert await harness.state().get_state() is None
    assert len(harness.session.calls) == 1
    prompt = harness.session.calls[0]
    assert isinstance(prompt, SendMessage)
    assert prompt.text == f"Необходима таймзона /{USER_COMMANDS.set_tz}"


async def test_exit_command_flushes_delete_queue_before_clearing_active_fsm(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.tts}")
    invocation = harness.invocations[0]
    assert invocation.callback is SpeechInitHandler
    assert await harness.state().get_state() == SpeechFSM.send_speech.state
    assert invocation.user_data is not None
    queued_message = invocation.user_data["delete_queue"][0]
    assert len(harness.session.calls) == 2
    harness.session.calls.clear()

    await harness.message(f"/{USER_COMMANDS.exit}")

    exit_invocation = harness.invocations[-1]
    assert exit_invocation.callback is exit_flow
    assert exit_invocation.state_before == SpeechFSM.send_speech.state
    assert exit_invocation.user_data is invocation.user_data
    assert invocation.user_data["delete_queue"] == []
    assert await harness.state().get_state() is None
    assert len(harness.session.calls) == 2
    deletion, answer = harness.session.calls
    assert isinstance(deletion, DeleteMessage)
    assert (deletion.chat_id, deletion.message_id) == (
        queued_message.chat.id,
        queued_message.message_id,
    )
    assert isinstance(answer, SendMessage)
    assert answer.text.startswith("Режим завершён.")


async def test_callback_reaches_delete_handler_and_shares_injected_user_data(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.set_tz}")
    message_invocation = harness.invocations[0]
    harness.session.calls.clear()
    harness.invocations.clear()
    harness.create_user.reset_mock()

    await harness.feed(callback_update(deleteMessageButtonPrefix))

    invocation = harness.invocations[0]
    assert invocation.callback is delete_message
    assert invocation.user_data is message_invocation.user_data
    assert invocation.state_before == TimezoneFSM.set_timezone.state
    assert len(harness.session.calls) == 1
    deletion = harness.session.calls[0]
    assert isinstance(deletion, DeleteMessage)
    assert (deletion.chat_id, deletion.message_id) == (USER_ID, 42)
    harness.create_user.assert_not_awaited()


async def test_inline_query_reaches_choice_handler_without_message_side_effects(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    assert await harness.feed(inline_update("lst only-choice")) is True

    assert len(harness.invocations) == 1
    assert harness.invocations[0].callback is send_choice
    harness.create_user.assert_awaited_once_with(
        user_id=USER_ID, user_name="Dispatcher Test"
    )
    assert len(harness.session.calls) == 1
    answer = harness.session.calls[0]
    assert isinstance(answer, AnswerInlineQuery)
    assert answer.inline_query_id == "inline-3"
    assert len(answer.results) == 1
    article = answer.results[0]
    assert isinstance(article, InlineQueryResultArticle)
    content = article.input_message_content
    assert isinstance(content, InputTextMessageContent)
    assert "<b>only-choice</b>" in content.message_text


async def test_exception_reaches_registered_error_handler_with_admin_injection(
    dispatcher_harness: DispatcherHarness,
) -> None:
    harness = dispatcher_harness
    await harness.message(f"/{USER_COMMANDS.set_tz}")
    harness.session.calls.clear()
    harness.set_timezone.side_effect = RuntimeError("offline persistence failed")

    await harness.message("3")

    assert harness.invocations[-1].callback is _set_timezone
    assert len(harness.session.calls) == len(ADMIN_IDS)
    for method, admin_id in zip(harness.session.calls, ADMIN_IDS, strict=True):
        assert isinstance(method, SendDocument)
        assert method.chat_id == admin_id
        assert method.caption is not None
        assert "Error: offline persistence failed" in method.caption
        assert "User: @dispatcher_test" in method.caption
        assert isinstance(method.document, BufferedInputFile)
        assert method.document.filename == "traceback.txt"
        assert b"_set_timezone" in method.document.data


@pytest.mark.parametrize(
    "update",
    [
        {"update_id": 10, "message": raw_message("short unmatched text")},
        {"update_id": 11, "message": raw_message("/unknown_command")},
        callback_update("unknown_callback"),
        inline_update("unknown_inline"),
    ],
    ids=["text", "command", "callback", "inline"],
)
async def test_unmatched_updates_do_not_invoke_unrelated_handlers(
    dispatcher_harness: DispatcherHarness, update: dict[str, object]
) -> None:
    harness = dispatcher_harness
    assert await harness.feed(update) is UNHANDLED
    assert harness.invocations == []
    assert harness.session.calls == []
    harness.create_user.assert_not_awaited()
    harness.get_timezone.assert_not_awaited()
    harness.set_timezone.assert_not_awaited()
