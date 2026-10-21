import datetime
from datetime import time

import pytest
from sqlalchemy.exc import IntegrityError, StatementError

from services.entities.road_settings import RoadSettings
from services.repositories.road_settings import RoadSettingsRepository, DEFAULT_SETTINGS
from tests.mocks.db import use_db


@pytest.mark.asyncio
@use_db
async def test_get_default_value():
    settings = await RoadSettingsRepository.get_user_settings(1)
    assert settings == DEFAULT_SETTINGS


@pytest.mark.asyncio
@use_db
async def test_set_settings():
    settings = RoadSettings(
        time_focused=time(minute=5),
        time_relax=time(minute=10),
    )
    await RoadSettingsRepository.set_user_settings(1, settings)
    received_settings = await RoadSettingsRepository.get_user_settings(1)
    # Note: tzinfo might be lost or changed during DB storage in SQLite
    assert received_settings.time_focused.minute == settings.time_focused.minute
    assert received_settings.time_relax.minute == settings.time_relax.minute


@pytest.mark.asyncio
@use_db
async def test_set_setting_by_name():
    setting_name = "time_focused"
    setting_new_value = time(minute=5)

    with pytest.raises((IntegrityError, StatementError, TypeError)):
        await RoadSettingsRepository.update_user_setting(1, setting_name, 10)

    await RoadSettingsRepository.update_user_setting(
        user_id=1, setting_name=setting_name, new_setting_value=setting_new_value
    )

    current_settings = await RoadSettingsRepository.get_user_settings(1)
    assert getattr(current_settings, setting_name).minute == setting_new_value.minute
