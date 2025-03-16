import datetime
from datetime import time

import pytest
from tortoise.exceptions import IntegrityError

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
        time_focused=time(minute=5, tzinfo=datetime.timezone.utc),
        time_relax=time(minute=10, tzinfo=datetime.timezone.utc),
    )
    await RoadSettingsRepository.set_user_settings(1, settings)
    received_settings = await RoadSettingsRepository.get_user_settings(1)
    assert received_settings.time_focused == settings.time_focused
    assert received_settings == settings


@pytest.mark.asyncio
@use_db
async def test_set_setting_by_name():
    setting_name = "time_focused"
    setting_new_value = time(minute=5, tzinfo=datetime.timezone.utc)

    with pytest.raises(IntegrityError):
        await RoadSettingsRepository.update_user_setting(1, setting_name, 10)

    await RoadSettingsRepository.update_user_setting(
        user_id=1, setting_name=setting_name, new_setting_value=setting_new_value
    )

    current_settings = await RoadSettingsRepository.get_user_settings(1)
    assert getattr(current_settings, setting_name) == setting_new_value
