# Remove the hardcoded GKFeed content filter

- STATUS: OPEN
- PRIORITY: 1

## Problem

`GkfeedApi.get_user_items` currently discards every item unless its link contains `porn` or `porno365`, while also excluding `unixporn`. This removes YouTube, TikTok, and the other supported feed sources before the item processor can select their views. The method also contains a block of commented temporary filters.

## Plan

1. Remove the hardcoded link filter and obsolete commented filtering code from the API client.
2. If content filtering is required, express it as an explicit caller option with a neutral default that returns all items.
3. Add tests with ordinary, adult, and empty links to define the API client's behavior.
4. Verify that feed-specific routing remains in `GkfeedItemProcessorExtension`.

## Acceptance criteria

- `get_user_items` returns all valid API items by default, regardless of source domain.
- Empty links remain handled without breaking iteration.
- No temporary commented filters remain in the method.
- Tests cover YouTube, TikTok, Pornhub, Porno365, Unixporn, and an empty link.

