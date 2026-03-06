# Add support for vkvideo.ru links

- STATUS: CLOSED
- PRIORITY: 1

## Plan
1. [x] Update `bot/filters/vk.py` to support `vkvideo.ru` links.
2. [x] Update `bot/services/ytdlp/options_manager.py` to recognize `vkvideo.ru` domain.
3. [x] Check `bot/handlers/text/ytdlp_short.py` for `vkvideo.ru` support if needed.
4. [x] Verify changes with a new test case in `bot/tests/filters/test_vk.py` (if it exists) or create one.
5. [x] Run existing tests to ensure no regressions.
