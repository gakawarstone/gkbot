import pytest

from handlers.user.road.settings.callback import EditSettingsHandler
from handlers.user.road.settings.edit.get_new_setting_value import (
    GetNewSettingValueHandler,
    InvalidTimeInput,
)
from handlers.user.road.settings.start import InitSettingsHandler
from handlers.user.road.states import FSM
from services.repositories.road_settings import DEFAULT_SETTINGS, RoadSettingsRepository
from tests.mocks.db import use_db
from tests.mocks.message import fake_event, make_fake_callback, make_fake_message
from tests.mocks.state import fake_state
from tests.mocks.user_data import MockedUserDataExtension
from ui.keyboards.pomodoro import PomodoroSettingsMarkup


class MockedEditSettingsHandler(MockedUserDataExtension, EditSettingsHandler):
    pass


@pytest.mark.asyncio
@use_db
async def test_staying_in_menu_after_settings_markup_sent():
    handler = InitSettingsHandler(event=fake_event, state=fake_state)
    await handler.handle()
    assert await handler.state.get_state() == FSM.menu


@pytest.mark.asyncio
@use_db
async def test_edit_settings():
    markup = PomodoroSettingsMarkup.get_settings_dialog(DEFAULT_SETTINGS)
    buttons = [button for row in markup.inline_keyboard for button in row]
    values = {"time_focused": 25, "time_relax": 5}
    callbacks = {button.callback_data for button in buttons}
    assert callbacks == {f"{PomodoroSettingsMarkup.prefix}:{name}" for name in values}

    for button in buttons:
        assert button.callback_data is not None
        setting_name = button.callback_data.split(":")[1]
        handler = MockedEditSettingsHandler(
            event=make_fake_callback(button.callback_data), state=fake_state
        )
        await handler.handle()
        assert await handler.state.get_state() == FSM.get_new_setting_value

        await GetNewSettingValueHandler(
            event=make_fake_message(str(values[setting_name])),
            state=fake_state,
            data=handler.user_data,
        ).handle()
        assert await handler.state.get_state() == FSM.menu

    settings = await RoadSettingsRepository.get_user_settings(1)
    assert settings.time_focused.minute == 25
    assert settings.time_relax.minute == 5


@pytest.mark.asyncio
@use_db
async def test_invalid_setting_value_does_not_change_settings():
    for value in ("abc", "-1", "60"):
        handler = MockedEditSettingsHandler(
            event=make_fake_callback(f"{PomodoroSettingsMarkup.prefix}:time_focused"),
            state=fake_state,
        )
        await handler.handle()
        with pytest.raises(InvalidTimeInput):
            await GetNewSettingValueHandler(
                event=make_fake_message(value), state=fake_state, data=handler.user_data
            ).handle()
        assert await RoadSettingsRepository.get_user_settings(1) == DEFAULT_SETTINGS
