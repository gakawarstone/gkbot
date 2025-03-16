import pytest

from tests.mocks.db import use_db
from tests.mocks.message import fake_event, make_fake_callback, make_fake_message
from tests.mocks.state import fake_state
from tests.mocks.user_data import MockedUserDataExtension
from services.entities.road_settings import RoadSettings
from services.repositories.road_settings import DEFAULT_SETTINGS
from handlers.user.road.pomodoro.pomodoro import PomodoroHandler
from handlers.user.road.settings.start import InitSettingsHandler
from handlers.user.road.settings.callback import EditSettingsHandler
from handlers.user.road.settings.edit.get_new_setting_value import (
    GetNewSettingValueHandler,
)
from handlers.user.road.states import FSM
from ui.keyboards.pomodoro import PomodoroSettingsMarkup


class MockedEditSettingsHandler(MockedUserDataExtension, EditSettingsHandler):
    pass


@pytest.fixture()
def buttons() -> list[dict]:
    settings_markup = PomodoroSettingsMarkup.get_settings_dialog(DEFAULT_SETTINGS)
    return [b[0] for b in settings_markup.model_dump()["inline_keyboard"]]


@pytest.mark.asyncio
async def test_undefined_settings_in_markup(buttons):
    for button in buttons:
        data = button["callback_data"]

        setting_name = data.split(":")[1]
        if setting_name not in RoadSettings.__dataclass_fields__:
            pytest.fail(f"Setting name {setting_name} defined only in markup")


@pytest.mark.asyncio
@use_db
async def test_staying_in_menu_after_settings_markup_sendet():
    handler = InitSettingsHandler(event=fake_event, state=fake_state)
    await handler.handle()
    assert await handler.state.get_state() == FSM.menu


def test_selection_setting_to_edit():
    pass


@pytest.mark.asyncio
@use_db
async def test_edit_settings():
    settings_markup = PomodoroSettingsMarkup.get_settings_dialog(DEFAULT_SETTINGS)
    # TODO: buttons iterator
    settings = settings_markup.model_dump()["inline_keyboard"]

    for setting in settings:
        data = setting[0]["callback_data"]
        event = make_fake_callback(data)
        state = fake_state
        handler = MockedEditSettingsHandler(event=event, state=state)

        await handler.handle()

        assert handler.ctx.setting_name == data.split(":")[1]
        assert await handler.state.get_state() == FSM.get_new_setting_value

        get_new_settings_value_handler = GetNewSettingValueHandler(
            event=make_fake_message("10"),  # FIXME: message with number
            state=state,
            data=handler.user_data,
        )
        await get_new_settings_value_handler.handle()

        new_setting_value = get_new_settings_value_handler.ctx.setting_new_value
        setting_name = data.split(":")[1]
        current_settings = await PomodoroHandler(fake_event).settings
        assert getattr(current_settings, setting_name) == new_setting_value
