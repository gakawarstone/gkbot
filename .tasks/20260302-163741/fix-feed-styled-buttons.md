# Fix styled buttons in feed

- STATUS: OPEN
- PRIORITY: 1

## Problem
The `InlineKeyboardButton` in `bot/modules/feed/ui/keyboards/__init__.py` uses `style="primary"` and `style="danger"`. These parameters were introduced in recent Bot API versions but may not be supported for all bots or clients, often causing the Telegram API to reject the message (Error 400). This results in feed items not being sent or buttons not appearing to work.

## Plan
1.  **Modify `bot/modules/feed/ui/keyboards/__init__.py`**:
    *   Remove the `style` parameter from `InlineKeyboardButton` in `_get_feed_buttons_row`.
    *   Add emojis to `FeedMarkupButtons` to provide visual cues (e.g., ✅ for "Keep" and 🗑️ for "Delete").
2.  **Verify**:
    *   Run linting on the modified file.
    *   Ensure no logic changes are introduced to the `callback_data`.
