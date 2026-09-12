# Remove confirmed dead symbols

- STATUS: OPEN
- PRIORITY: 3

## Problem

Several symbols have no consumers and no framework registration path. They add misleading states, fields, methods, and model choices to the codebase.

## Plan

1. Remove unused `FSM.start_timer` and `FSM.pomodoro` states.
2. Remove `_BookProperty.event_code` and its unused values.
3. Remove `YtDlp._get_video_input_file`.
4. Remove unused `OpenRouterModel` values `MICROSOFT_PHI_4_REASONING`, `DEEPSEEK_DEEPSEEK_R1_0528`, `STEP_35`, and `KIMI_K25`.
5. Recheck `GPT_OSS_120` after the archived summarizer is deleted and remove it if no runtime consumer remains.
6. Preserve `GEMMA_4` and `GPT_5_6_LUNA`, which are used.
7. Search for dynamic or framework references before each deletion.

## Acceptance criteria

- Each removed symbol has no remaining reference.
- Active FSM flows, book callbacks, TikTok extraction, and LLM selection still work.
- Focused tests and static checks pass.

