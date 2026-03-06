# Fix BOT_TOKEN is required error in tests

- STATUS: CLOSED
- PRIORITY: 1

## Problem
Tests fail with `ValueError: BOT_TOKEN is required` because `bot/configs/env.py` strictly requires `BOT_TOKEN` and `ADMIN_IDS` even when running non-integration tests.

## Solution
Created `bot/tests/conftest.py` to set dummy environment variables before tests run. This avoids adding test-specific logic to the production configuration file `bot/configs/env.py`.

### Changes
- Created `bot/tests/conftest.py` with dummy values for:
    - `BOT_TOKEN`
    - `ADMIN_IDS`
    - `SQLDIALECT`
    - `DB_USER`
    - `DB_PASSWORD`
    - `DB_HOST`
    - `DB_PORT`
    - `DB_NAME`
