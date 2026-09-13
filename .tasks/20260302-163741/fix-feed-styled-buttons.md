# Add colored buttons in feed

- STATUS: OPEN
- PRIORITY: 1

## Problem
The feed item buttons in `bot/modules/feed/ui/keyboards/__init__.py` currently use plain text (`"Оставить"` / `"Убрать"`) with no `style`. `aiogram==3.26.0` (`InlineKeyboardButton.style`) supports `'success'` (green), `'danger'` (red), and `'primary'` (blue), so we should use colored buttons for visual cues.

## Plan
1.  **Modify `bot/modules/feed/ui/keyboards/__init__.py`**:
    *   Add `style="success"` to the Keep button and `style="danger"` to the Delete button in `_get_feed_buttons_row`.
    *   Keep button text as `"Оставить"` / `"Убрать"` (no emoji prefix).
2.  **Verify**:
    *   Run linting on the modified file.
    *   Ensure no logic changes are introduced to the `callback_data`.
    *   Verify markup builds and sends via Bot API without Error 400.
