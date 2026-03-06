# Fix edge-tts functionality

- STATUS: COMPLETED
- PRIORITY: 1

## Plan
1.  Read the `edge-tts` implementation in `bot/services/tts/providers.py` and the corresponding tests in `bot/tests/services/test_text_to_speech.py`. [DONE]
2.  Run the tests using `make test FILE=bot/tests/services/test_text_to_speech.py` to confirm the failure. [DONE]
3.  Investigate the cause of the failure (e.g., API changes, dependency issues). [DONE]
4.  Apply the fix to `bot/services/tts/providers.py`. [DONE - Updated package versions]
5.  Verify the fix by running the tests again. [DONE]
6.  Run linting using `make lint FILE=bot/services/tts/providers.py`. [DONE]

## Changes
- Updated `edge-tts` to latest version (7.2.7) and `aiohttp` to 3.13.3. This fixed the `403 Forbidden` error from Microsoft Edge TTS.
- Fixed a broken `patch("builtins.open")` in `bot/tests/services/test_text_to_speech.py` that was causing `open` to be globally mocked across tests, leading to `TypeError` in `netrc`.
