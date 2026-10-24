import asyncio

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.methods import (
    DeleteEphemeralMessage,
    DeleteMessage,
    EditEphemeralMessageText,
    EditMessageText,
    SendMessage,
)

from tests.mocks.status import StatusHarness
from utils.status_message import send_status, temporary_status


@pytest.mark.parametrize("chat_type", ["group", "supergroup"])
async def test_group_status_is_personal_and_uses_ephemeral_operations(
    monkeypatch: pytest.MonkeyPatch, chat_type: str
) -> None:
    harness = StatusHarness(monkeypatch, chat_type)
    message = harness.message.model_copy(
        update={"message_thread_id": 13, "is_topic_message": True}
    )
    async with temporary_status(message, "Wait") as status:
        await status.edit_text("Processing")
    send, edit, delete = harness.methods
    assert isinstance(send, SendMessage)
    assert send.chat_id == harness.chat.id
    assert send.message_thread_id == 13
    parameters = send.ephemeral_message_parameters
    assert parameters is not None
    assert parameters.receiver_user_id == harness.user.id
    assert send.receiver_user_id == harness.user.id
    assert isinstance(edit, EditEphemeralMessageText)
    assert isinstance(delete, DeleteEphemeralMessage)
    assert edit.chat_id == delete.chat_id == harness.chat.id
    assert edit.receiver_user_id == delete.receiver_user_id == harness.user.id
    assert edit.ephemeral_message_id == delete.ephemeral_message_id == 91
    assert edit.text == "Processing"


async def test_expired_callback_can_reuse_its_existing_ephemeral_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = StatusHarness(monkeypatch)
    harness.send_error = TelegramBadRequest(
        method=SendMessage(chat_id=-42, text="Wait"),
        message="Bad Request: query is too old",
    )
    async with temporary_status(
        harness.response(1, ephemeral=True),
        "Wait",
        callback=harness.callback,
        reuse_message=True,
    ):
        pass
    assert [type(method) for method in harness.methods] == [
        SendMessage,
        EditEphemeralMessageText,
        DeleteEphemeralMessage,
    ]


async def test_old_server_ignoring_parameters_does_not_duplicate_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = StatusHarness(monkeypatch)
    harness.supported = False
    async with temporary_status(harness.message, "Wait") as status:
        await status.edit_text("Processing")
    assert [type(method) for method in harness.methods] == [
        SendMessage,
        EditMessageText,
        DeleteMessage,
    ]


@pytest.mark.parametrize(
    "description",
    [
        "Bad Request: ephemeral messages are not supported",
        "Bad Request: CHAT_ADMIN_REQUIRED",
    ],
)
@pytest.mark.parametrize("reuse", [False, True])
async def test_rejected_ephemeral_send_falls_back(
    monkeypatch: pytest.MonkeyPatch, description: str, reuse: bool
) -> None:
    harness = StatusHarness(monkeypatch)
    harness.send_error = TelegramBadRequest(
        method=SendMessage(chat_id=-42, text="Wait"), message=description
    )
    async with temporary_status(
        harness.message, "Wait", callback=harness.callback, reuse_message=reuse
    ) as status:
        await status.edit_text("Processing")
    attempt, fallback, edit, delete = harness.methods
    assert isinstance(attempt, SendMessage)
    assert isinstance(fallback, EditMessageText if reuse else SendMessage)
    if isinstance(fallback, SendMessage):
        assert fallback.ephemeral_message_parameters is None
        assert fallback.receiver_user_id is None
    assert isinstance(edit, EditMessageText)
    assert isinstance(delete, DeleteMessage)


@pytest.mark.parametrize("network_error", [False, True])
async def test_unrelated_or_ambiguous_send_errors_are_not_retried(
    monkeypatch: pytest.MonkeyPatch, network_error: bool
) -> None:
    harness = StatusHarness(monkeypatch)
    error_type = TelegramNetworkError if network_error else TelegramBadRequest
    harness.send_error = error_type(
        method=SendMessage(chat_id=-42, text="Wait"),
        message="timeout" if network_error else "Bad Request: can't parse entities",
    )
    with pytest.raises(error_type):
        await send_status(harness.message, "Wait")
    assert len(harness.methods) == 1


@pytest.mark.parametrize("ephemeral", [False, True])
@pytest.mark.parametrize("failure", ["success", "download", "cancel"])
async def test_cleanup_failure_does_not_mask_result_or_cancellation(
    monkeypatch: pytest.MonkeyPatch,
    ephemeral: bool,
    failure: str,
) -> None:
    harness = StatusHarness(monkeypatch, "supergroup" if ephemeral else "private")
    harness.cleanup_error = TelegramBadRequest(
        method=DeleteMessage(chat_id=-42, message_id=2),
        message="Bad Request: message to delete not found",
    )

    async def operation() -> None:
        async with temporary_status(harness.message, "Wait"):
            if failure == "cancel":
                raise asyncio.CancelledError
            if failure == "download":
                raise ValueError("download failed")

    if failure == "cancel":
        with pytest.raises(asyncio.CancelledError):
            await operation()
    elif failure == "download":
        with pytest.raises(ValueError, match="download failed"):
            await operation()
    else:
        await operation()
