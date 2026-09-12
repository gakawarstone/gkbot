# Migrate callback payloads to aiogram CallbackData

- STATUS: OPEN
- PRIORITY: 3

## Problem

Six button modules maintain custom data classes, serializers, deserializers, builders, and permissive boolean parsing. The protocols have already diverged and accept malformed values inconsistently.

## Plan

1. Inventory the YouTube, VK, Pornhub, Porno365, Matreshka, and Sasflix payload formats.
2. Define typed `aiogram.filters.callback_data.CallbackData` models with explicit prefixes and fields.
3. Migrate keyboard builders and handler filters one source at a time.
4. Decide whether old callback payloads need a temporary compatibility path.
5. Add round-trip and malformed-payload tests for every model.

## Acceptance criteria

- All six button families use aiogram `CallbackData` models.
- Ad hoc serializers and deserializers are removed.
- Invalid boolean and enum values are rejected.
- Callback tests cover round trips and malformed input.

