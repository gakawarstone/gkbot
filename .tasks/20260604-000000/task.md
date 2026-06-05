# Dead Code Check

Checked project-owned source from `bot/main.py` reachability, `vulture`, and manual grep verification.

## Likely Safe To Remove

- `bot/modules/feed/handlers/_exceptions.py:1` - `UnavailableMediaException` is never imported or raised.
- `bot/services/agents/summarizator.py:7` - `Summarizator` is not referenced anywhere.
- `bot/services/tiktok/extractor/proxytok.py:12` - `ProxyTok` is disabled/commented out in `bot/services/tiktok/extractor/__init__.py` and not used.
- `bot/services/vk.py:6` - `VKService` and `try_to_extract_video_link_from_post` are never imported or called.
- `bot/utils/chunks.py:10` - `split_str_into_chunks` is unused. `chunks` in the same file is used by the Platonus converter.
- `bot/handlers/prompt/gpt.py:24` - `send_unavailable_message` is unused.
- `bot/handlers/user/cvision.py:57` - `AnswerHandler._render` is unused; the handler uses `_render_markdown` instead.
- `bot/modules/feed/handlers/views/video.py:10` - `_process_video_item` is unused. `VideoFeedItemView` itself is used by other feed views.
- `bot/services/ffmpeg.py:143` - `FfmpegService.make_slideshow_from_files` is unused.
- `bot/services/tiktok/extractor/snaptik/_decoder.py:33` - `from_string` is unused.
- `bot/services/tiktok/extractor/yt_dlp.py:54` - `_get_video_input_file` is unused.

## Lower Confidence Cleanup

- `bot/configs/commands.py:12` - `USER_COMMANDS.shiki` is not used as a command, though Shiki feed handling exists.
- `bot/handlers/user/books/states.py:9-10` - `show_test_book` and `change_book_property` states appear unused.
- `bot/services/llm/openrouter.py:11-15` - unused enum values: `MICROSOFT_PHI_4_REASONING`, `DEEPSEEK_DEEPSEEK_R1_0528`, `STEP_35`, `KIMI_K25`. Keep if intended as selectable model inventory.

## Ignored False Positives

- Tortoise ORM model fields such as `table`, `user_name`, `total_cnt`, etc.
- TypedDict/enum-style fields and callback-data fields that may be framework/introspection driven.
- aiogram handlers registered by reference in `setup()` functions.
